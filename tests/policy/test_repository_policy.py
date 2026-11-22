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

    def test_rejects_credentials(self):
        for path in ["src/.env", "src/config/secrets.json", "infra/server.key"]:
            with self.subTest(path=path):
                self.assertTrue(any(code == "SENSITIVE_OR_BINARY_ARTIFACT" for code, _ in policy.check_path(path)))


if __name__ == "__main__":
    unittest.main()
