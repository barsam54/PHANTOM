"""Do not combine historical CI evidence from unrelated revisions."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2] / "scripts/verify_governance_evidence_pair.py"
spec = importlib.util.spec_from_file_location("evidence_pair", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SHA = "a" * 40
CHECKOUT = "b" * 40


def proof(criterion, run, key):
    return {
        "status": "CHECK_OK", "criterion": criterion, "criterion_verified": True,
        "reused_existing_run": True,
        "new_build_or_test_invoked_by_verifier": False,
        "governance_acceptance": "OPEN", "historical_run_id": run,
        key: SHA, "historical_checkout_sha": CHECKOUT,
    }


def pair():
    return (proof("governance.policy_ci", 123, "historical_pr_head_sha"),
            proof("governance.dotnet_ci", 124, "historical_head_sha"))


class EvidencePairTests(unittest.TestCase):
    def test_matching_provenance_pair_is_scoped_not_accepted(self):
        policy, dotnet = pair()
        result = mod.verify_pair(policy, dotnet)
        self.assertEqual("PAIR_CHECK_OK", result["status"])
        self.assertTrue(result["pair_verified"])
        self.assertFalse(result["stage_accepted"])
        self.assertEqual("OPEN", result["governance_acceptance"])
        self.assertEqual(2, len(result["criteria_verified"]))

    def test_different_pr_heads_denied(self):
        policy, dotnet = pair()
        dotnet["historical_head_sha"] = "c" * 40
        self.assertEqual("PAIR_HEAD_SHA_MISMATCH", mod.verify_pair(policy, dotnet)["code"])

    def test_different_merge_checkouts_denied(self):
        policy, dotnet = pair()
        dotnet["historical_checkout_sha"] = "c" * 40
        self.assertEqual("PAIR_CHECKOUT_SHA_MISMATCH", mod.verify_pair(policy, dotnet)["code"])

    def test_reusing_same_workflow_run_twice_denied(self):
        policy, dotnet = pair()
        dotnet["historical_run_id"] = policy["historical_run_id"]
        self.assertEqual("PAIR_RUN_ID_COLLISION", mod.verify_pair(policy, dotnet)["code"])

    def test_off_criterion_receipt_denied(self):
        policy, dotnet = pair()
        dotnet["criterion"] = policy["criterion"]
        self.assertEqual("PAIR_RECEIPT_UNVERIFIED", mod.verify_pair(policy, dotnet)["code"])

    def test_fake_accepted_receipt_denied(self):
        policy, dotnet = pair()
        policy["governance_acceptance"] = "PASS"
        self.assertEqual("PAIR_RECEIPT_UNVERIFIED", mod.verify_pair(policy, dotnet)["code"])

    def test_missing_provider_verified_receipt_denied(self):
        policy, dotnet = pair()
        policy["criterion_verified"] = False
        self.assertEqual("PAIR_RECEIPT_UNVERIFIED", mod.verify_pair(policy, dotnet)["code"])

    def test_unpinned_sha_denied(self):
        policy, dotnet = pair()
        policy["historical_checkout_sha"] = "abc"
        self.assertEqual("PAIR_RECEIPT_UNVERIFIED", mod.verify_pair(policy, dotnet)["code"])


if __name__ == "__main__":
    unittest.main()
