"""Scoped evidence acceptance: real ZIP content, tamper rejection, and no-test rerun reuse."""
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

SRC = Path(__file__).resolve().parents[2] / "scripts/verify_governance_artifact.py"
spec = importlib.util.spec_from_file_location("evidence_readback", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SHA = "a" * 40
RUN = 92


def fixtures():
    cb = json.dumps({"gate": "GOV-P0", "status": "OPEN", "baseline": mod.BASELINE,
                     "capabilities": [{"id": key} for key in sorted(mod.CAPS)]}).encode()
    bb = b"## 12. P0 evidence fixture"
    inv = {"gate": "GOV-P0", "decision": "OPEN", "commit_sha": SHA,
           "contract_digest_sha256": mod.sha(cb),
           "baseline_digest_sha256": mod.sha(bb),
           "capabilities": [{"id": key, "contract_state": "OPEN", "verified": False}
                            for key in sorted(mod.CAPS)]}
    probe = {"phase": "GOV-P0", "overall_acceptance": "OPEN", "sha": SHA,
             "contract_sha256": mod.sha(cb), "all_steps_executed": False,
             "steps": [{"step": key, "code": "PENDING", "reason": "not verified",
                        "action": "collect evidence", "resume": "discover"} for key in mod.STEPS]}
    return cb, bb, inv, probe


def archive(inv, probe):
    out = io.BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as zipped:
        zipped.writestr("governance-inventory.json", json.dumps(inv))
        zipped.writestr("governance-phase0-ten-steps.json", json.dumps(probe))
    return out.getvalue()


def metadata(data):
    return {"id": 11, "name": "governance-inventory", "expired": False,
            "digest": "sha256:" + mod.sha(data),
            "workflow_run": {"id": RUN, "head_sha": SHA}}


def check(cb, bb, inv, probe, *, data=None, art=None):
    data = archive(inv, probe) if data is None else data
    return mod.inspect_archive(data, art or metadata(data), SHA, cb, bb)


class EvidenceContentTests(unittest.TestCase):
    def test_real_content_is_read_and_does_not_self_accept_gate(self):
        result = check(*fixtures())
        self.assertEqual("CHECK_OK", result["status"])
        self.assertTrue(result["content_readback_verified"])
        self.assertEqual("OPEN", result["governance_acceptance"])

    def test_reject_false_pass(self):
        cb, bb, inv, probe = fixtures()
        inv["capabilities"][0]["verified"] = True
        self.assertEqual("FALSE_ACCEPTANCE_OR_COVERAGE", check(cb, bb, inv, probe)["code"])

    def test_reject_wrong_code_sha(self):
        cb, bb, inv, probe = fixtures()
        probe["sha"] = "b" * 40
        self.assertEqual("PINNED_SOURCE_MISMATCH", check(cb, bb, inv, probe)["code"])

    def test_reject_changed_baseline(self):
        cb, bb, inv, probe = fixtures()
        self.assertEqual("PINNED_SOURCE_MISMATCH", check(cb, bb + b"edited", inv, probe)["code"])

    def test_reject_false_full_execution(self):
        cb, bb, inv, probe = fixtures()
        probe["all_steps_executed"] = True
        self.assertEqual("PROBE_CRITERIA_INVALID", check(cb, bb, inv, probe)["code"])

    def test_reject_tampered_archive(self):
        cb, bb, inv, probe = fixtures()
        original = archive(inv, probe)
        self.assertEqual("ARCHIVE_DIGEST_MISMATCH",
                         check(cb, bb, inv, probe, data=original + b"tampered",
                               art=metadata(original))["code"])

    def test_reject_missing_content(self):
        cb, bb, inv, probe = fixtures()
        out = io.BytesIO()
        with ZipFile(out, "w") as zipped:
            zipped.writestr("governance-inventory.json", json.dumps(inv))
        self.assertEqual("EVIDENCE_CONTENT_MISSING",
                         check(cb, bb, inv, probe, data=out.getvalue())["code"])

    def test_scoped_reuse_without_running_ci_again(self):
        cb, bb, inv, probe = fixtures()
        data = archive(inv, probe)
        base = "https://api.github.com/repos/o/r/actions/"
        root = base + "runs/" + str(RUN)
        raw = "https://raw.githubusercontent.com/o/r/" + SHA + "/"
        readback = {
            root: json.dumps({"id": RUN, "name": "Repository Policy Guard",
                              "head_sha": SHA, "event": "pull_request",
                              "status": "completed", "conclusion": "success"}).encode(),
            root + "/jobs?per_page=100": json.dumps({"total_count": 1, "jobs": [
                {"status": "completed", "conclusion": "success"}]}).encode(),
            root + "/artifacts?per_page=100": json.dumps({"total_count": 1,
                "artifacts": [metadata(data)]}).encode(),
            raw + mod.CONTRACT: cb, raw + mod.BASELINE: bb,
            base + "artifacts/11/zip": data,
        }
        calls = []
        def fetch(url, token=None):
            calls.append(url)
            return readback[url]
        with tempfile.TemporaryDirectory() as td:
            first = mod.verify_live("o/r", RUN, SHA, td, read=fetch)
            second = mod.verify_live("o/r", RUN, SHA, td, read=fetch)
            self.assertEqual("CHECK_OK", first["status"])
            self.assertEqual("CHECK_OK", second["status"])
            self.assertFalse(first["archive_reused"])
            self.assertTrue(second["archive_reused"])
            self.assertFalse(second["ci_tests_reexecuted"])
            self.assertEqual(1, calls.count(base + "artifacts/11/zip"))
            self.assertEqual(2, calls.count(root))
            # Content cache must not override a changed artifact digest.
            new = dict(metadata(data))
            new["digest"] = "sha256:" + "e" * 64
            readback[root + "/artifacts?per_page=100"] = json.dumps({
                "total_count": 1, "artifacts": [new]}).encode()
            third = mod.verify_live("o/r", RUN, SHA, td, read=fetch)
            self.assertEqual("ARCHIVE_DIGEST_MISMATCH", third["code"])


if __name__ == "__main__":
    unittest.main()
