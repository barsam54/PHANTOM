"""Integration of existing validation modules through one fail-closed entrypoint."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("evidence_pipeline", ROOT / "scripts/governance_evidence_pipeline.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
from test_governance_criteria_matrix import fixtures
SHA = "a" * 40
CURRENT = "d" * 40
TREE = "e" * 40
OTHER_TREE = "f" * 40

def source(sha, tree):
    return {"sha": sha, "commit": {"tree": {"sha": tree}}}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.contract, self.policy, self.dotnet, _, self.pair = fixtures()
        self.old = source(SHA, TREE)
        self.current = source(CURRENT, TREE)

    def evaluate(self):
        return mod.evaluate(self.contract, self.policy, self.dotnet,
                            self.old, self.current)

    def test_identical_tree_stays_unaccepted(self):
        result, details = self.evaluate()
        self.assertEqual("VERIFIED_SCOPE_ONLY", result["status"])
        self.assertEqual("REUSABLE", result["reuse_decision"])
        self.assertEqual(6, result["criteria_discovered"])
        self.assertEqual(2, result["historical_ci_criteria_verified"])
        self.assertEqual(0, result["current_phase_criteria_verified"])
        self.assertEqual("OPEN", result["governance_acceptance"])
        self.assertFalse(result["phase_evidence_verification_completed"])
        self.assertEqual("PAIR_CHECK_OK", details["pair"]["status"])

    def test_changed_tree_denies_reuse_not_entire_evidence_audit(self):
        self.current = source(CURRENT, OTHER_TREE)
        result, details = self.evaluate()
        self.assertEqual("VERIFIED_SCOPE_ONLY", result["status"])
        self.assertEqual("BLOCKED", result["reuse_decision"])
        self.assertEqual("REUSE_INPUT_TREE_CHANGED", result["reuse_code"])
        self.assertFalse(details["reuse"]["reuse_allowed"])
        self.assertEqual(0, result["accepted_capabilities"])

    def test_mismatched_ci_heads_rejected_before_any_reuse(self):
        self.dotnet["historical_head_sha"] = "b" * 40
        result, details = self.evaluate()
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("PAIR_HEAD_SHA_MISMATCH", result["code"])
        self.assertEqual({}, details)

    def test_missing_source_criteria_blocks_pipeline(self):
        self.contract["capabilities"].pop()
        result, _ = self.evaluate()
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", result["code"])

    def test_forged_provider_receipt_blocks_pipeline(self):
        self.policy["criterion_verified"] = False
        result, _ = self.evaluate()
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("PAIR_RECEIPT_UNVERIFIED", result["code"])

    def test_missing_old_tree_is_not_acceptable_change(self):
        self.old = source(SHA, "")
        result, _ = self.evaluate()
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("REUSE_TREE_NOT_ATTESTED", result["code"])

    def test_missing_evidence_is_not_an_errorless_success(self):
        self.dotnet = {}
        result, _ = self.evaluate()
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("OPEN", result["governance_acceptance"])
        self.assertEqual("evidence", result["resume"])


if __name__ == "__main__":
    unittest.main()
