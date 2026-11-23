"""Negative admission tests for the source-first / reuse-first decision contract."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("policy", ROOT / "scripts/check_repository_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class SourceFirstTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        target = self.root / policy.SOURCE_DECISION_FILE
        target.parent.mkdir(parents=True)
        self.source = json.loads((ROOT / policy.SOURCE_DECISION_FILE).read_text(encoding="utf-8"))
        self.target = target
        self.write(self.source)

    def write(self, doc):
        self.target.write_text(json.dumps(doc), encoding="utf-8")

    def codes(self):
        return {x["code"] for x in policy.check_source_first_decision(self.root)}

    def test_current_official_review_shape_accepted(self):
        self.assertEqual(set(), self.codes())

    def test_missing_decision_is_rejected_with_remedy(self):
        self.target.unlink()
        denials = policy.check_source_first_decision(self.root)
        self.assertEqual("GOV_SOURCE_DECISION_MISSING", denials[0]["code"])
        self.assertTrue(denials[0]["action"])
        self.assertTrue(denials[0]["resume"])

    def test_missing_official_sources_is_rejected(self):
        self.source["official_sources"] = []
        self.write(self.source)
        self.assertIn("GOV_OFFICIAL_SOURCE_INVALID", self.codes())

    def test_unapproved_domain_is_rejected(self):
        self.source["official_sources"][0]["url"] = "https://untrusted.example/docs"
        self.write(self.source)
        self.assertIn("GOV_OFFICIAL_SOURCE_INVALID", self.codes())

    def test_missing_version_and_verification_is_rejected(self):
        self.source["official_sources"][0].pop("reviewed_version")
        self.write(self.source)
        self.assertIn("GOV_OFFICIAL_SOURCE_INVALID", self.codes())

    def test_single_option_without_reuse_comparison_is_rejected(self):
        self.source["candidate_solutions"] = self.source["candidate_solutions"][:1]
        self.write(self.source)
        self.assertIn("GOV_REUSE_COMPARISON_MISSING", self.codes())

    def test_invalid_choice_is_rejected(self):
        self.source["chosen_option"] = "invented_controller"
        self.write(self.source)
        self.assertIn("GOV_SOURCE_CHOICE_UNREFERENCED", self.codes())


if __name__ == "__main__":
    unittest.main()
