"""Governance inventory must be honest about what it cannot verify."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/governance_inventory.py"
spec = importlib.util.spec_from_file_location("governance_inventory", SCRIPT)
inventory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory_module)


class GovernanceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        doc = self.root / "docs/architecture"
        doc.mkdir(parents=True)
        contract = json.loads(
            (inventory_module.ROOT / inventory_module.CONTRACT_PATH).read_text(encoding="utf-8")
        )
        (self.root / inventory_module.CONTRACT_PATH).write_text(
            json.dumps(contract), encoding="utf-8"
        )
        (doc / "BASELINE.md").write_text("# test baseline", encoding="utf-8")

    def test_does_not_treat_file_presence_as_pass(self):
        ev = self.root / "docs/evidence"
        ev.mkdir(parents=True)
        (ev / "sml02-pass-claimed.md").write_text("PASS claimed", encoding="utf-8")
        old = inventory_module.git_revision
        inventory_module.git_revision = lambda root: "1" * 40
        try:
            record = inventory_module.inventory(self.root)
        finally:
            inventory_module.git_revision = old
        self.assertEqual("OPEN", record["decision"])
        self.assertFalse(record["historical_evidence_verified"])
        self.assertEqual(1, record["historical_evidence_files_found"])
        self.assertEqual(1, len(record["evidence_integrity_inventory"]))
        self.assertEqual("sml02-pass-claimed.md",
            Path(record["evidence_integrity_inventory"][0]["path"]).name)
        self.assertEqual(64, len(record["evidence_integrity_inventory"][0]["sha256"]))
        self.assertFalse(record["evidence_integrity_inventory"][0]["verified"])
        self.assertEqual("READ_ONLY_DISCOVERY_NOT_ACCEPTANCE", record["kind"])
        self.assertTrue(all(not cap["verified"] for cap in record["capabilities"]))
        self.assertFalse(record["dashboard"]["projects_synced"])
        barrier = record["merge_barrier_history"]
        self.assertEqual("NEGATIVE_REQUIRED_CHECK_BLOCKED", barrier["observation"])
        self.assertFalse(barrier["verified"])
        self.assertFalse(barrier["current_ruleset_revalidated"])
        self.assertFalse(barrier["direct_push_rejection_tested"])

    def test_rejects_false_accepted_contract(self):
        target = self.root / inventory_module.CONTRACT_PATH
        doc = json.loads(target.read_text(encoding="utf-8"))
        doc["status"] = "PASS"
        target.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "GOV_PREMATURE_ACCEPTANCE"):
            inventory_module.inventory(self.root)

    def test_markdown_report_explicitly_open(self):
        old = inventory_module.git_revision
        inventory_module.git_revision = lambda root: "2" * 40
        try:
            report = inventory_module.inventory(self.root)
        finally:
            inventory_module.git_revision = old
        text = inventory_module.markdown(report)
        self.assertIn("GOV-P0 OPEN", text)
        self.assertIn("NOT VERIFIED", text)
        self.assertIn("Projects synchronized: NO", text)
        self.assertIn("Protected-main historical evidence", text)
        self.assertIn("Direct push denial tested: NO", text)


if __name__ == "__main__":
    unittest.main()
