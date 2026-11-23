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
    return contract, policy, dotnet, reuse


def check(contract=None, policy=None, dotnet=None, reuse=None):
    values = fixtures()
    c, p, d, r = (values[0] if contract is None else contract,
                  values[1] if policy is None else policy,
                  values[2] if dotnet is None else dotnet,
                  values[3] if reuse is None else reuse)
    return module.build_matrix(c, policy_receipt=p, dotnet_receipt=d, reuse_decision=r)


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
        c, p, d, r = fixtures()
        c["capabilities"].pop()
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", check(contract=c)["code"])

    def test_duplicate_criterion_blocks(self):
        c, p, d, r = fixtures()
        c["capabilities"][-1]["id"] = c["capabilities"][0]["id"]
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", check(contract=c)["code"])

    def test_self_certified_capability_pass_blocks(self):
        c, p, d, r = fixtures()
        c["capabilities"][0]["state"] = "PASS"
        self.assertEqual("MATRIX_CRITERIA_INCOMPLETE", check(contract=c)["code"])

    def test_forged_policy_receipt_blocks(self):
        c, p, d, r = fixtures()
        p["criterion_verified"] = False
        self.assertEqual("MATRIX_PROOF_INVALID", check(policy=p)["code"])

    def test_wrong_dotnet_criterion_blocks(self):
        c, p, d, r = fixtures()
        d["criterion"] = "governance.policy_ci"
        self.assertEqual("MATRIX_PROOF_INVALID", check(dotnet=d)["code"])

    def test_missing_reuse_check_blocks(self):
        self.assertEqual("MATRIX_REUSE_NOT_CHECKED", check(reuse={})["code"])

    def test_false_allowed_reuse_blocks(self):
        c, p, d, r = fixtures()
        r["reuse_allowed"] = True
        self.assertEqual("MATRIX_REUSE_CONTRADICTION", check(reuse=r)["code"])

    def test_same_tree_reuse_still_does_not_accept_stage(self):
        c, p, d, r = fixtures()
        r = {"criterion": "governance.dotnet_ci", "status": "REUSABLE",
             "code": "IDENTICAL_REPOSITORY_TREE", "reuse_allowed": True,
             "current_stage_acceptance": "NOT_ASSESSED"}
        out = check(reuse=r)
        self.assertEqual("ALLOWED_FOR_IDENTICAL_TREE_ONLY", out["dotnet_current_revision_reuse"])
        self.assertEqual(0, out["accepted_capabilities"])
        self.assertEqual("OPEN", out["governance_acceptance"])


if __name__ == "__main__":
    unittest.main()
