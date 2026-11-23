"""Cross-run reuse acceptance: pinned provenance, exact content and negative cases."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("prior_evidence", ROOT / "scripts/verify_prior_governance_evidence.py")
# Import the companion module in the same manner as direct CLI invocation.
import sys
sys.path.insert(0, str(ROOT / "scripts"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
import test_verify_governance_artifact as sample

HEAD = "c" * 40
CHECKOUT = "a" * 40
RUN = 92
API = "https://api.github.com/repos/o/r"
RAW = "https://raw.githubusercontent.com/o/r/" + CHECKOUT + "/"


def build_read_map(cb, bb, inv, probe):
    return {
        API + "/actions/runs/92": {
            "id": RUN, "head_sha": HEAD, "name": "Repository Policy Guard",
            "event": "pull_request", "status": "completed", "conclusion": "success"},
        API + "/actions/runs/92/jobs?per_page=100": {
            "total_count": 1, "jobs": [{"status": "completed", "conclusion": "success"}]},
        API + "/actions/runs/92/artifacts?per_page=100": {
            "total_count": 1, "artifacts": [{
                "id": 11, "name": "governance-inventory", "expired": False,
                "digest": "sha256:" + "f" * 64,
                "workflow_run": {"id": RUN, "head_sha": HEAD},
            }]},
        API + "/commits/" + CHECKOUT: {
            "sha": CHECKOUT, "parents": [{"sha": "b" * 40}, {"sha": HEAD}]},
        RAW + module.CONTRACT: cb,
        RAW + module.BASELINE: bb,
    }


def setup_fixture(temp):
    cb, bb, inv, probe = sample.fixtures()
    (Path(temp) / "governance-inventory.json").write_text(json.dumps(inv), encoding="utf-8")
    (Path(temp) / "governance-phase0-ten-steps.json").write_text(json.dumps(probe), encoding="utf-8")
    records = build_read_map(cb, bb, inv, probe)
    calls = []
    def fake_fetch(url, token=None):
        calls.append(url)
        datum = records[url]
        return datum if isinstance(datum, bytes) else json.dumps(datum).encode()
    return records, calls, fake_fetch


class PriorEvidenceTests(unittest.TestCase):
    def test_real_historical_receipt_is_reused_and_rechecked(self):
        with tempfile.TemporaryDirectory() as td:
            records, calls, fetch = setup_fixture(td)
            first = module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)
            second = module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)
            self.assertEqual("CHECK_OK", first["status"])
            self.assertEqual("CHECK_OK", second["status"])
            self.assertTrue(second["reused_existing_run"])
            self.assertFalse(second["new_build_or_test_invoked_by_verifier"])
            self.assertEqual("NOT_ASSESSED", second["current_revision_acceptance"])
            self.assertEqual("OPEN", second["governance_acceptance"])
            self.assertEqual(2, calls.count(API + "/actions/runs/92"))

    def test_rejects_wrong_run_commit(self):
        with tempfile.TemporaryDirectory() as td:
            records, _, fetch = setup_fixture(td)
            records[API + "/actions/runs/92"]["head_sha"] = "d" * 40
            self.assertEqual("RUN_PROVENANCE_INVALID",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])

    def test_rejects_failed_job(self):
        with tempfile.TemporaryDirectory() as td:
            records, _, fetch = setup_fixture(td)
            records[API + "/actions/runs/92/jobs?per_page=100"]["jobs"][0]["conclusion"] = "failure"
            self.assertEqual("JOBS_UNVERIFIED",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])

    def test_rejects_wrong_merge_parent(self):
        with tempfile.TemporaryDirectory() as td:
            records, _, fetch = setup_fixture(td)
            records[API + "/commits/" + CHECKOUT]["parents"][1]["sha"] = "d" * 40
            self.assertEqual("MERGE_LINEAGE_INVALID",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])

    def test_rejects_forged_pass_in_historical_report(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, fetch = setup_fixture(td)
            p = Path(td) / "governance-inventory.json"
            inv = json.loads(p.read_text())
            inv["capabilities"][0]["verified"] = True
            p.write_text(json.dumps(inv))
            self.assertEqual("FALSE_ACCEPTANCE_OR_COVERAGE",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])

    def test_rejects_wrong_baseline_digest(self):
        with tempfile.TemporaryDirectory() as td:
            records, _, fetch = setup_fixture(td)
            records[RAW + module.BASELINE] = b"## 12. P0 changed baseline"
            self.assertEqual("PINNED_SOURCE_MISMATCH",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])

    def test_rejects_missing_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            records, _, fetch = setup_fixture(td)
            records[API + "/actions/runs/92/artifacts?per_page=100"]["artifacts"] = []
            self.assertEqual("ARTIFACT_MISSING_OR_DUPLICATE",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])

    def test_rejects_absent_extracted_report(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, fetch = setup_fixture(td)
            (Path(td) / "governance-inventory.json").unlink()
            self.assertEqual("EVIDENCE_CONTENT_MISSING",
                module.verify_extracted("o/r", RUN, HEAD, td, read=fetch)["code"])


if __name__ == "__main__":
    unittest.main()
