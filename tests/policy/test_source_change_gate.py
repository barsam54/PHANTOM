"""PR-scoped source-first admission negative tests."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "source_gate", ROOT / "scripts/check_source_first_changes.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class SourceChangeGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        target = self.root / gate.RECORD
        target.parent.mkdir(parents=True)
        (self.root / gate.CONTRACT).write_bytes((ROOT / gate.CONTRACT).read_bytes())
        self.record = json.loads((ROOT / gate.RECORD).read_text(encoding="utf-8"))
        self.record["scope"] = ["src/Example.cs", gate.RECORD]
        self.target = target
        self.write()

    def write(self):
        self.target.write_text(json.dumps(self.record), encoding="utf-8")

    def codes(self, files=None):
        files = files if files is not None else ["src/Example.cs", gate.RECORD]
        return {item["code"] for item in gate.evaluate(self.root, files)}

    def test_matching_change_scope_and_official_sources_pass(self):
        self.assertEqual(set(), self.codes())

    def test_unreviewed_changed_file_blocks(self):
        self.assertIn("GOV_SOURCE_CHANGE_UNREVIEWED",
                      self.codes(["src/Example.cs", "src/NewTool.cs", gate.RECORD]))

    def test_stale_decision_scope_blocks(self):
        self.assertIn("GOV_SOURCE_SCOPE_STALE",
                      self.codes(["src/Example.cs"]))

    def test_missing_record_blocks(self):
        self.target.unlink()
        self.assertIn("GOV_SOURCE_RECORD_UNREADABLE", self.codes())

    def test_unreviewed_status_blocks(self):
        self.record["status"] = "PROPOSED"
        self.write()
        self.assertIn("GOV_SOURCE_REVIEW_NOT_CONFIRMED", self.codes())

    def test_unofficial_host_blocks(self):
        self.record["official_sources"][0]["url"] = "https://example.org/docs"
        self.write()
        self.assertIn("GOV_OFFICIAL_SOURCE_INVALID", self.codes())

    def test_absent_source_version_blocks(self):
        self.record["official_sources"][0].pop("reviewed_version")
        self.write()
        self.assertIn("GOV_OFFICIAL_SOURCE_INVALID", self.codes())

    def test_duplicate_scope_blocks(self):
        self.record["scope"].append("src/Example.cs")
        self.write()
        self.assertIn("GOV_SOURCE_SCOPE_INVALID", self.codes())

    def test_malformed_base_sha_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "GOV_BASE_SHA_INVALID"):
            gate.changed_files(ROOT, "main")


if __name__ == "__main__":
    unittest.main()
