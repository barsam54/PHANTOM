"""Ten-step phase 0 governance diagnostic: no false PASS, actionable stops."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/governance_phase0_probe.py"
spec = importlib.util.spec_from_file_location("governance_phase0_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class Phase0TenStepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "docs/architecture").mkdir(parents=True)
        (self.root / "docs/evidence").mkdir(parents=True)
        (self.root / "src/Phantom.AgentFramework").mkdir(parents=True)
        src = json.loads((probe.ROOT / probe.CONTRACT_FILE).read_text(encoding="utf-8"))
        (self.root / probe.CONTRACT_FILE).write_text(json.dumps(src), encoding="utf-8")
        (self.root / src["baseline"]).write_text(
            "Six simultaneous, complementary capabilities", encoding="utf-8")
        (self.root / "src/Phantom.AgentFramework/Phantom.AgentFramework.csproj").write_text(
            "Microsoft.Agents.AI.Workflows", encoding="utf-8")

    def run_local(self):
        old = probe.git_sha
        probe.git_sha = lambda root: "f" * 40
        try:
            return probe.run_probe(self.root)
        finally:
            probe.git_sha = old

    def test_ten_ordered_steps_all_probed_but_not_accepted(self):
        record = self.run_local()
        self.assertEqual(10, record["step_count"])
        self.assertEqual(list(probe.STEPS), [s["step"] for s in record["steps"]])
        self.assertEqual("OPEN", record["overall_acceptance"])
        self.assertFalse(record["all_steps_executed"])
        self.assertFalse(record["runner_mutated_repository"])
        self.assertEqual("NOT_IMPLEMENTED", record["steps"][4]["state"])
        self.assertEqual("BLOCKED", record["steps"][7]["state"])
        self.assertEqual("NOT_IMPLEMENTED", record["steps"][9]["state"])
        for step in record["steps"]:
            for field in ("code", "stage", "reason", "evidence", "action", "resume"):
                self.assertTrue(step[field], (step["step"], field))

    def test_historical_pass_filename_not_certified(self):
        (self.root / "docs/evidence/claimed-PASS.md").write_text("PASS")
        record = self.run_local()
        self.assertEqual(1, record["historical_evidence_files_discovered"])
        self.assertFalse(record["historical_evidence_verified"])
        self.assertEqual("OPEN", record["overall_acceptance"])

    def test_baseline_mismatch_blocks_only_affected_step(self):
        (self.root / "docs/architecture/BASELINE.md").write_text("no approved clause")
        record = self.run_local()
        self.assertEqual("BLOCKED", record["steps"][1]["state"])
        self.assertEqual("BASELINE_MISSING_OR_MISMATCH", record["steps"][1]["code"])
        self.assertEqual(10, record["step_count"])

    def test_contract_phase_order_change_rejected(self):
        path = self.root / probe.CONTRACT_FILE
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract["phase_steps"][0], contract["phase_steps"][1] = (
            contract["phase_steps"][1], contract["phase_steps"][0])
        path.write_text(json.dumps(contract), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "GOV_STAGE_CONTRACT_MISMATCH"):
            self.run_local()

    def test_markdown_never_reports_end_to_end_pass(self):
        output = probe.summary(self.run_local())
        self.assertIn("Acceptance: OPEN", output)
        self.assertIn("Rollback execution: NOT TESTED", output)
        self.assertIn("GitHub Projects sync: NOT TESTED", output)


if __name__ == "__main__":
    unittest.main()
