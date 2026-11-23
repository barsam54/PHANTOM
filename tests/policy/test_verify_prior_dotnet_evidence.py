"""Fail-closed historical .NET receipt checks, with no test re-execution."""
import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("dotnet_prior", ROOT / "scripts/verify_prior_dotnet_evidence.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
HEAD = "c" * 40
CHECKOUT = "a" * 40
RUN = 92
API = "https://api.github.com/repos/o/r"
RAW = "https://raw.githubusercontent.com/o/r/" + CHECKOUT + "/"


def fixture(tmp):
    baseline = b"## 12. P0"
    contract = b'{"gate":"GOV-P0","status":"OPEN"}'
    log = b"Total tests: 24\nPassed: 24\nFailed: 0\n"
    dig = lambda v: hashlib.sha256(v).hexdigest()
    doc = {
        "schema_version": "phantom.governance.dotnet-receipt.v1",
        "criterion_id": module.CRITERION, "checkout_sha": CHECKOUT,
        "contract_sha256": dig(contract), "baseline_sha256": dig(baseline),
        "test_project": module.PROJECT, "test_runner": "Microsoft.Testing.Platform",
        "test_step_outcome": "success", "job_status_at_receipt": "success",
        "test_log_sha256": dig(log), "test_log_bytes": len(log), "acceptance": "OPEN",
    }
    (Path(tmp) / "dotnet-tests.log").write_bytes(log)
    (Path(tmp) / "dotnet-ci-receipt.json").write_text(json.dumps(doc))
    lookup = {
        API + "/actions/runs/92": {"id": RUN, "head_sha": HEAD, "event": "pull_request",
            "name": module.WORKFLOW, "status": "completed", "conclusion": "success"},
        API + "/actions/runs/92/jobs?per_page=100": {"total_count": 1,
            "jobs": [{"status": "completed", "conclusion": "success",
                "steps": [{"name": "Run MSTest using Microsoft.Testing.Platform",
                           "conclusion": "success"}]}]},
        API + "/actions/runs/92/artifacts?per_page=100": {"total_count": 1,
            "artifacts": [{"name": module.NAME, "id": 10, "expired": False,
                "digest": "sha256:" + "f" * 64,
                "workflow_run": {"id": RUN, "head_sha": HEAD}}]},
        API + "/commits/" + CHECKOUT: {"sha": CHECKOUT, "parents": [
            {"sha": "b" * 40}, {"sha": HEAD}]},
        RAW + module.BASELINE: baseline, RAW + module.CONTRACT: contract,
    }
    def read(url, token=None):
        val = lookup[url]
        return val if isinstance(val, bytes) else json.dumps(val).encode()
    return lookup, read


class DotnetEvidenceTests(unittest.TestCase):
    def test_historical_receipt_repeatable(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            first = module.verify("o/r", RUN, HEAD, td, read=read)
            second = module.verify("o/r", RUN, HEAD, td, read=read)
            self.assertEqual(first, second)
            self.assertEqual("CHECK_OK", second["status"])
            self.assertFalse(second["new_build_or_test_invoked_by_verifier"])
            self.assertEqual("OPEN", second["governance_acceptance"])

    def test_refuses_nonzero_test_failure_in_log(self):
        with tempfile.TemporaryDirectory() as td:
            _, read = fixture(td)
            path = Path(td) / "dotnet-tests.log"
            log = b"Total tests: 24\nPassed: 23\nFailed: 1\n"
            path.write_bytes(log)
            receipt = Path(td) / "dotnet-ci-receipt.json"
            data = json.loads(receipt.read_text())
            data["test_log_sha256"] = hashlib.sha256(log).hexdigest()
            data["test_log_bytes"] = len(log)
            receipt.write_text(json.dumps(data))
            self.assertEqual("DOTNET_LOG_FAILURE_MARKER",
                module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_forged_pass_in_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            path = Path(td) / "dotnet-ci-receipt.json"
            doc = json.loads(path.read_text())
            doc["acceptance"] = "PASS"
            path.write_text(json.dumps(doc))
            self.assertEqual("DOTNET_RECEIPT_MISMATCH", module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_tampered_log(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            (Path(td) / "dotnet-tests.log").write_bytes(b"tampered test result")
            self.assertEqual("DOTNET_RECEIPT_MISMATCH", module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_wrong_checkout_lineage(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            data[API + "/commits/" + CHECKOUT]["parents"][1]["sha"] = "d" * 40
            self.assertEqual("DOTNET_MERGE_LINEAGE_INVALID", module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_failed_test_step(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            data[API + "/actions/runs/92/jobs?per_page=100"]["jobs"][0]["steps"][0]["conclusion"] = "failure"
            self.assertEqual("DOTNET_TEST_EXECUTION_MISSING", module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_expired_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            data[API + "/actions/runs/92/artifacts?per_page=100"]["artifacts"][0]["expired"] = True
            self.assertEqual("DOTNET_ARTIFACT_PROVENANCE_INVALID", module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_wrong_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            data[RAW + module.BASELINE] = b"not the pinned baseline"
            self.assertEqual("DOTNET_RECEIPT_MISMATCH", module.verify("o/r", RUN, HEAD, td, read=read)["code"])

    def test_refuses_missing_test_log(self):
        with tempfile.TemporaryDirectory() as td:
            data, read = fixture(td)
            (Path(td) / "dotnet-tests.log").unlink()
            self.assertEqual("DOTNET_ARTIFACT_CONTENT_MISSING", module.verify("o/r", RUN, HEAD, td, read=read)["code"])


if __name__ == "__main__":
    unittest.main()
