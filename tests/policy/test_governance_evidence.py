"""Negative and positive CI receipt checks; no mocked source may confer gate PASS."""
import importlib.util
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "scripts/validate_governance_evidence.py"
spec = importlib.util.spec_from_file_location("ci_evidence", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SHA = "a" * 40
RUN = 42


def fixtures():
    run = {"id": RUN, "head_sha": SHA, "name": "Repository Policy Guard",
           "event": "pull_request", "status": "completed", "conclusion": "success"}
    jobs = {"total_count": 1, "jobs": [{"status": "completed", "conclusion": "success"}]}
    artifacts = {"total_count": 1, "artifacts": [{
        "id": 123, "name": "governance-inventory", "expired": False,
        "size_in_bytes": 100, "digest": "sha256:" + "b" * 64,
        "workflow_run": {"id": RUN, "head_sha": SHA}
    }]}
    return run, jobs, artifacts


def check(run, jobs, artifacts, criterion="governance.policy_ci", sha=SHA):
    return mod.verify(run, jobs, artifacts, expected_sha=sha, run_id=RUN,
                      criterion=criterion)


class EvidenceReceiptTests(unittest.TestCase):
    def test_valid_receipt_limits_its_own_claim(self):
        result = check(*fixtures())
        self.assertEqual("CHECK_OK", result["status"])
        self.assertTrue(result["verified"])
        self.assertFalse(result["artifact_contents_readback"])
        self.assertFalse(result["artifact_criterion_coverage_verified"])
        self.assertFalse(result["reused_as_stage_acceptance"])
        self.assertEqual("OPEN", result["governance_acceptance"])

    def test_wrong_sha_denied(self):
        run, jobs, arts = fixtures()
        run["head_sha"] = "c" * 40
        self.assertEqual("RUN_IDENTITY_MISMATCH", check(run, jobs, arts)["code"])

    def test_failed_run_denied(self):
        run, jobs, arts = fixtures()
        run["conclusion"] = "failure"
        self.assertEqual("RUN_NOT_SUCCESSFUL", check(run, jobs, arts)["code"])

    def test_failed_job_denied(self):
        run, jobs, arts = fixtures()
        jobs["jobs"][0]["conclusion"] = "failure"
        self.assertEqual("JOB_NOT_SUCCESSFUL", check(run, jobs, arts)["code"])

    def test_expired_artifact_denied(self):
        run, jobs, arts = fixtures()
        arts["artifacts"][0]["expired"] = True
        self.assertEqual("ARTIFACT_PROVENANCE_INVALID", check(run, jobs, arts)["code"])

    def test_wrong_artifact_sha_denied(self):
        run, jobs, arts = fixtures()
        arts["artifacts"][0]["workflow_run"]["head_sha"] = "c" * 40
        self.assertEqual("ARTIFACT_PROVENANCE_INVALID", check(run, jobs, arts)["code"])

    def test_invalid_digest_denied(self):
        run, jobs, arts = fixtures()
        arts["artifacts"][0]["digest"] = "sha256:tampered"
        self.assertEqual("ARTIFACT_PROVENANCE_INVALID", check(run, jobs, arts)["code"])

    def test_missing_artifact_denied(self):
        run, jobs, arts = fixtures()
        arts["artifacts"].clear()
        self.assertEqual("ARTIFACT_MISSING_OR_DUPLICATE", check(run, jobs, arts)["code"])

    def test_duplicate_artifact_denied(self):
        run, jobs, arts = fixtures()
        arts["artifacts"].append(arts["artifacts"][0].copy())
        self.assertEqual("ARTIFACT_MISSING_OR_DUPLICATE", check(run, jobs, arts)["code"])

    def test_unrecognized_criterion_denied(self):
        self.assertEqual("UNKNOWN_CRITERION",
                         check(*fixtures(), criterion="forged.pass")["code"])


if __name__ == "__main__":
    unittest.main()
