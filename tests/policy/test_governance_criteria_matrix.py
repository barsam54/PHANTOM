"""Six-criterion acceptance mapping never promotes historical CI to whole-stage PASS."""
import importlib.util
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("criteria_matrix", ROOT / "scripts/governance_criteria_matrix.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CAPS = module.CRITERIA


def fixtures():
    contract = {"gate": "GOV-P0", "status": "OPEN",
                "capabilities": [{"id": x, "state": "OPEN", "proof": x+" criterion"} for x in CAPS]}
    policy = {"status": "CHECK_OK", "criterion": "governance.policy_ci",
              "criterion_verified": True, "reused_existing_run": True,
              "new_build_or_test_invoked_by_verifier": False,
              "governance_acceptance": "OPEN", "historical_run_id": 11,
              "historical_checkout_sha": "a"*40}
    dotnet = dict(policy, criterion="governance.dotnet_ci", historical_run_id=12,
                  historical_checkout_sha="b"*40)
    reuse = {"criterion": "governance.dotnet_ci", "status": "BLOCKED",
             "code": "REUSE_INPUT_TREE_CHANGED", "reuse_allowed": False}
    pair = {"status": "PAIR_CHECK_OK", "pair_verified": True,
            "stage_accepted": False, "governance_acceptance": "OPEN",
            "historical_pr_head_sha": "c"*40,
            "historical_checkout_sha": "a"*40,
            "run_ids": [11, 12]}
    policy["historical_pr_head_sha"] = "c"*40
    dotnet["historical_head_sha"] = "c"*40
    dotnet["historical_checkout_sha"] = "a"*40
    return contract, policy, dotnet, reuse, pair


def check(contract=None, policy=None, dotnet=None, reuse=None, pair=None):
    values = fixtures()
    c, p, d, r, b = (values[0] if contract is None else contract,
                  values[1] if policy is None else policy,
                  values[2] if dotnet is None else dotnet,
                  values[3] if reuse is None else reuse,
                  values[4] if pair is None else pair)
    return module.build_matrix(c, policy_receipt=p, dotnet_receipt=d, reuse_decision=r,
                               pair_receipt=b)


class MatrixTests(unittest.TestCase):
    def test_complete_readonly_inventory_with_two_historical_proofs(self):
        report = check()
        self.assertEqual("INVENTORIED_OPEN", report["status"])
        self.assertEqual(6, report["criteria_count"])
        self.assertEqual(0, report["accepted_capabilities"])
        self.assertEqual(2, report["historical_proofs_checked"])
        self.assertFalse(report["single_lifecycle_integration_proven"])
        self.assertTrue(all(x["acceptance"] == "OPEN" for x in report["capabilities"]))
        self.assertTrue(all(not x["current_revision_accepted"] for x in report["historical_proofs"]))

    def test_missing_criterion_blocks(self):
        c, p, d, r, b = fixtures()
        c["capabilities"].pop()
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", check(contract=c)["code"])

    def test_duplicate_criterion_blocks(self):
        c, p, d, r, b = fixtures()
        c["capabilities"][-1]["id"] = c["capabilities"][0]["id"]
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", check(contract=c)["code"])

    def test_self_certified_capability_pass_blocks(self):
        c, p, d, r, b = fixtures()
        c["capabilities"][0]["state"] = "PASS"
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", check(contract=c)["code"])

    def test_forged_policy_receipt_blocks(self):
        c, p, d, r, b = fixtures()
        p["criterion_verified"] = False
        self.assertEqual("MATRIX_PROOF_INVALID", check(policy=p)["code"])

    def test_wrong_dotnet_criterion_blocks(self):
        c, p, d, r, b = fixtures()
        d["criterion"] = "governance.policy_ci"
        self.assertEqual("MATRIX_PROOF_INVALID", check(dotnet=d)["code"])

    def test_missing_reuse_check_blocks(self):
        self.assertEqual("MATRIX_REUSE_NOT_CHECKED", check(reuse={})["code"])

    def test_false_allowed_reuse_blocks(self):
        c, p, d, r, b = fixtures()
        r["reuse_allowed"] = True
        self.assertEqual("MATRIX_REUSE_CONTRADICTION", check(reuse=r)["code"])

    def test_missing_pair_blocks(self):
        self.assertEqual("MATRIX_UNBOUND_EVIDENCE_PAIR", check(pair={})["code"])

    def test_different_pr_head_blocks_even_if_both_receipts_pass(self):
        c, p, d, r, b = fixtures()
        d["historical_head_sha"] = "d" * 40
        self.assertEqual("MATRIX_UNBOUND_EVIDENCE_PAIR", check(dotnet=d)["code"])

    def test_different_checked_out_source_blocks(self):
        c, p, d, r, b = fixtures()
        d["historical_checkout_sha"] = "d" * 40
        self.assertEqual("MATRIX_UNBOUND_EVIDENCE_PAIR", check(dotnet=d)["code"])

    def test_forged_pair_decision_blocks(self):
        c, p, d, r, b = fixtures()
        b["stage_accepted"] = True
        self.assertEqual("MATRIX_UNBOUND_EVIDENCE_PAIR", check(pair=b)["code"])

    def test_same_tree_reuse_still_does_not_accept_stage(self):
        c, p, d, r, b = fixtures()
        r = {"criterion": "governance.dotnet_ci", "status": "REUSABLE",
             "code": "IDENTICAL_REPOSITORY_TREE", "reuse_allowed": True,
             "current_stage_acceptance": "NOT_ASSESSED"}
        out = check(reuse=r)
        self.assertEqual("ALLOWED_FOR_IDENTICAL_TREE_ONLY", out["dotnet_current_revision_reuse"])
        self.assertEqual(0, out["accepted_capabilities"])
        self.assertEqual("OPEN", out["governance_acceptance"])


if __name__ == "__main__":
    unittest.main()
