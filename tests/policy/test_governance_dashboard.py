"""Read-only dashboard rendering checks: no false PASS, no mixed revisions."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("gov_dash", ROOT / "scripts/render_governance_dashboard.py")
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)


def sample():
    caps = [{"id": key, "contract_state": "OPEN", "verified": False,
             "next_proof": "evidence <required>"} for key in dashboard.CAP_NAMES]
    steps = [{"step": key, "state": "CHECK_OK" if i < 3 else "NOT_IMPLEMENTED",
              "code": "GOV_EXPECTED", "reason": "not proven <test>",
              "action": "collect proofs", "resume": "discover"}
             for i, key in enumerate(dashboard.STAGE_NAMES)]
    inv = {"gate": "GOV-P0", "decision": "OPEN", "commit_sha": "a"*40,
           "contract_digest_sha256": "b"*64, "capabilities": caps,
           "historical_evidence_files_found": 2, "remaining": ["test"]}
    probe = {"phase": "GOV-P0", "overall_acceptance": "OPEN",
             "sha": "a"*40, "contract_sha256": "b"*64,
             "all_steps_executed": False, "steps": steps}
    return inv, probe


class DashboardTests(unittest.TestCase):
    def test_renders_honest_html_svg_and_summary(self):
        inv, probe = sample()
        view = dashboard.model(inv, probe)
        self.assertEqual("OPEN", view["acceptance"])
        self.assertEqual(0, view["accepted_capabilities"])
        self.assertEqual(3, view["stage_categories"]["CHECK_OK"])
        self.assertEqual(7, view["stage_categories"]["NOT_IMPLEMENTED"])
        self.assertEqual(0, view["stage_categories"]["BLOCKED"])
        self.assertIn("0 / 6 accepted", dashboard.dashboard_html(view))
        self.assertIn("&lt;required&gt;", dashboard.dashboard_html(view))
        self.assertIn("&lt;test&gt;", dashboard.dashboard_html(view))
        self.assertIn("<svg", dashboard.dashboard_svg(view))
        self.assertIn("0 / 6 controls accepted", dashboard.dashboard_summary(view))
        self.assertFalse(view["projects_synced"])

    def test_rejects_revision_mismatch(self):
        inv, probe = sample()
        probe["sha"] = "c"*40
        with self.assertRaisesRegex(ValueError, "SOURCE_REVISION_MISMATCH"):
            dashboard.model(inv, probe)

    def test_rejects_contract_digest_mismatch(self):
        inv, probe = sample()
        probe["contract_sha256"] = "c"*64
        with self.assertRaisesRegex(ValueError, "CONTRACT_HASH_MISMATCH"):
            dashboard.model(inv, probe)

    def test_rejects_false_acceptance(self):
        inv, probe = sample()
        inv["capabilities"][0]["verified"] = True
        with self.assertRaisesRegex(ValueError, "FALSE_CAPABILITY_ACCEPTANCE"):
            dashboard.model(inv, probe)

    def test_rejects_incomplete_steps(self):
        inv, probe = sample()
        probe["steps"][4]["action"] = ""
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_REMEDY"):
            dashboard.model(inv, probe)

    def test_rejects_missing_or_reordered_steps(self):
        inv, probe = sample()
        probe["steps"].reverse()
        with self.assertRaisesRegex(ValueError, "TEN_STAGES_REQUIRED"):
            dashboard.model(inv, probe)

    def test_rejects_proclaimed_execution(self):
        inv, probe = sample()
        probe["all_steps_executed"] = True
        with self.assertRaisesRegex(ValueError, "PROBE_MUST_NOT_CLAIM_EXECUTION"):
            dashboard.model(inv, probe)


if __name__ == "__main__":
    unittest.main()
