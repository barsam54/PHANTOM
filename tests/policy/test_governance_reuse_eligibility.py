"""Conservative criterion-scoped evidence reuse: same tree or deny."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("reuse_check", ROOT / "scripts/check_governance_reuse_eligibility.py")
import sys
sys.path.insert(0, str(ROOT / "scripts"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
OLD = "a" * 40
CURRENT = "b" * 40
TREE = "c" * 40
DIFF = "d" * 40


def proof(criterion="governance.dotnet_ci"):
    return {"status": "CHECK_OK", "criterion_verified": True,
            "criterion": criterion, "reused_existing_run": True,
            "historical_checkout_sha": OLD, "new_build_or_test_invoked_by_verifier": False,
            "governance_acceptance": "OPEN"}


def commit(sha, tree):
    return {"sha": sha, "commit": {"tree": {"sha": tree}}}


def check(criterion="governance.dotnet_ci", evidence=None, old_tree=TREE, new_tree=TREE):
    return mod.assess(criterion=criterion,
                      historical_proof=proof(criterion) if evidence is None else evidence,
                      historical_commit=commit(OLD, old_tree),
                      current_commit=commit(CURRENT, new_tree))


class ReuseAdmissionTests(unittest.TestCase):
    def test_same_tree_different_commits_eligible_without_stage_pass(self):
        r = check()
        self.assertEqual("REUSABLE", r["status"])
        self.assertTrue(r["reuse_allowed"])
        self.assertEqual("NOT_ASSESSED", r["current_stage_acceptance"])
        self.assertEqual("OPEN", r["governance_acceptance"])

    def test_changed_test_or_source_tree_denied(self):
        r = check(new_tree=DIFF)
        self.assertEqual("REUSE_INPUT_TREE_CHANGED", r["code"])
        self.assertFalse(r["reuse_allowed"])

    def test_policy_criterion_distinct_from_dotnet(self):
        r = check(criterion="governance.policy_ci", evidence=proof("governance.dotnet_ci"))
        self.assertEqual("REUSE_PROOF_UNVERIFIED", r["code"])

    def test_unknown_criterion_denied(self):
        self.assertEqual("REUSE_UNKNOWN_CRITERION", check(criterion="fake.pass")["code"])

    def test_claimed_verified_without_provenance_denied(self):
        p = proof()
        p["criterion_verified"] = False
        self.assertEqual("REUSE_PROOF_UNVERIFIED", check(evidence=p)["code"])

    def test_not_reused_original_run_denied(self):
        p = proof()
        p["reused_existing_run"] = False
        self.assertEqual("REUSE_PROOF_UNVERIFIED", check(evidence=p)["code"])

    def test_false_governance_acceptance_denied(self):
        p = proof()
        p["governance_acceptance"] = "PASS"
        self.assertEqual("REUSE_PROOF_UNVERIFIED", check(evidence=p)["code"])

    def test_missing_old_tree_denied(self):
        r = check(old_tree="")
        self.assertEqual("REUSE_TREE_NOT_ATTESTED", r["code"])

    def test_unpinned_historical_commit_denied(self):
        r = mod.assess(criterion="governance.dotnet_ci", historical_proof=proof(),
                       historical_commit=commit(CURRENT, TREE),
                       current_commit=commit(CURRENT, TREE))
        self.assertEqual("REUSE_REVISION_NOT_ATTESTED", r["code"])

    def test_positive_policy_case_with_same_tree(self):
        self.assertEqual("REUSABLE", check(criterion="governance.policy_ci")["status"])


if __name__ == "__main__":
    unittest.main()
