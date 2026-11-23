"""Unit tests for the PHANTOM repository policy (stdlib unittest)."""
import importlib.util
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / "scripts" / "check_repository_policy.py"
spec = importlib.util.spec_from_file_location("repository_policy", GUARD)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class RepositoryPolicyTests(unittest.TestCase):
    def test_approved_paths(self):
        for path in ["global.json", "PHANTOM.slnx", "src/App/Program.cs",
                     "tests/Phantom.Infrastructure.Tests/Test1.cs",
                     "docs/architecture/BASELINE.md", ".github/workflows/repository-policy.yml"]:
            with self.subTest(path=path):
                self.assertEqual([], policy.check_path(path))

    def test_rejects_loose_root_file_with_reason(self):
        issues = policy.check_path("Test1.cs")
        self.assertTrue(any(code == "ROOT_FILE_NOT_ALLOWED" for code, _ in issues))

    def test_rejects_backups_and_data(self):
        for path in ["backups/archive.zip", "data/market.csv", "logs/runtime.log"]:
            with self.subTest(path=path):
                self.assertTrue(any(code == "ROOT_DIRECTORY_NOT_ALLOWED" for code, _ in policy.check_path(path)))

    def test_rejects_generated_outputs(self):
        issues = policy.check_path("tests/Suite/bin/Debug/test.dll")
        self.assertTrue(any(code == "GENERATED_OUTPUT_TRACKED" for code, _ in issues))

    def test_rejects_model_weights(self):
        for path in ["infra/local-models/model.gguf",
                     "src/assets/weights.safetensors", "data/weights.ggml"]:
            with self.subTest(path=path):
                self.assertTrue(any(code == "SENSITIVE_OR_BINARY_ARTIFACT"
                    for code, _ in policy.check_path(path)))

    def test_rejects_credentials(self):
        for path in ["src/.env", "src/config/secrets.json", "infra/server.key"]:
            with self.subTest(path=path):
                self.assertTrue(any(code == "SENSITIVE_OR_BINARY_ARTIFACT" for code, _ in policy.check_path(path)))


    def test_governance_contract_is_valid(self):
        self.assertEqual([], policy.check_governance_contract())

    def test_governance_missing_contract_explains_remedy(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            issues = policy.check_governance_contract(Path(temp))
        self.assertEqual("GOV_CONTRACT_MISSING", issues[0]["code"])
        for field in ("code", "stage", "reason", "evidence", "action", "resume"):
            self.assertTrue(issues[0][field])

    def test_governance_rejects_premature_pass(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs/architecture").mkdir(parents=True)
            source = policy.ROOT / policy.GOVERNANCE_CONTRACT
            doc = json.loads(source.read_text(encoding="utf-8"))
            doc["status"] = "PASS"
            (root / policy.GOVERNANCE_CONTRACT).write_text(json.dumps(doc), encoding="utf-8")
            (root / "docs/architecture/BASELINE.md").write_text("test")
            (root / "docs/architecture/GOVERNANCE-CONTROLLER.md").write_text("test")
            issues = policy.check_governance_contract(root)
        self.assertIn("GOV_PREMATURE_ACCEPTANCE", [i["code"] for i in issues])

    def test_governance_rejects_missing_capability(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs/architecture").mkdir(parents=True)
            source = policy.ROOT / policy.GOVERNANCE_CONTRACT
            doc = json.loads(source.read_text(encoding="utf-8"))
            doc["capabilities"] = doc["capabilities"][:-1]
            (root / policy.GOVERNANCE_CONTRACT).write_text(json.dumps(doc), encoding="utf-8")
            (root / "docs/architecture/BASELINE.md").write_text("test")
            (root / "docs/architecture/GOVERNANCE-CONTROLLER.md").write_text("test")
            issues = policy.check_governance_contract(root)
        self.assertIn("GOV_CAPABILITY_MISMATCH", [i["code"] for i in issues])


    def test_governance_sixth_capability_required(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs/architecture").mkdir(parents=True)
            doc = json.loads((policy.ROOT / policy.GOVERNANCE_CONTRACT).read_text(encoding="utf-8"))
            doc["capabilities"] = [c for c in doc["capabilities"] if c["id"] != "impact_rollback"]
            (root / policy.GOVERNANCE_CONTRACT).write_text(json.dumps(doc), encoding="utf-8")
            (root / "docs/architecture/BASELINE.md").write_text("fixture")
            (root / "docs/architecture/GOVERNANCE-CONTROLLER.md").write_text("fixture")
            issues = policy.check_governance_contract(root)
        self.assertIn("GOV_CAPABILITY_MISMATCH", [i["code"] for i in issues])

    def test_governance_impact_proof_fields_mandatory(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs/architecture").mkdir(parents=True)
            doc = json.loads((policy.ROOT / policy.GOVERNANCE_CONTRACT).read_text(encoding="utf-8"))
            doc["impact_rollback"]["required_fields"].remove("rollback_test_evidence")
            (root / policy.GOVERNANCE_CONTRACT).write_text(json.dumps(doc), encoding="utf-8")
            (root / "docs/architecture/BASELINE.md").write_text("fixture")
            (root / "docs/architecture/GOVERNANCE-CONTROLLER.md").write_text("fixture")
            issues = policy.check_governance_contract(root)
        self.assertIn("GOV_IMPACT_CRITERIA_INCOMPLETE", [i["code"] for i in issues])
        self.assertTrue(all(i.get("action") and i.get("resume") for i in issues))

    def test_governance_impact_cannot_self_mark_pass(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs/architecture").mkdir(parents=True)
            doc = json.loads((policy.ROOT / policy.GOVERNANCE_CONTRACT).read_text(encoding="utf-8"))
            doc["impact_rollback"]["state"] = "PASS"
            (root / policy.GOVERNANCE_CONTRACT).write_text(json.dumps(doc), encoding="utf-8")
            (root / "docs/architecture/BASELINE.md").write_text("fixture")
            (root / "docs/architecture/GOVERNANCE-CONTROLLER.md").write_text("fixture")
            issues = policy.check_governance_contract(root)
        self.assertIn("GOV_IMPACT_CONTRACT_MISSING", [i["code"] for i in issues])

if __name__ == "__main__":
    unittest.main()
