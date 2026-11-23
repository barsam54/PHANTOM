"""Optional Ollama integration must not cause model downloads or hosted access."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_local_ollama", ROOT / "scripts/check_local_ollama.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LocalOllamaProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.profile = Path(self.temp.name) / "model.json"
        self.source = json.loads(module.PROFILE.read_text(encoding="utf-8"))
        self.write()

    def write(self):
        self.profile.write_text(json.dumps(self.source), encoding="utf-8")

    def test_versioned_profile_is_disabled_by_default(self):
        item = module.validate_profile(self.profile)
        self.assertEqual("qwen3:4b", item["model"])
        self.assertIs(item["enabled_by_default"], False)
        self.assertIs(item["model_artifact_in_git"], False)

    def test_rejects_non_loopback_url(self):
        self.source["api_base"] = "http://192.0.2.1:11434"
        self.write()
        with self.assertRaisesRegex(ValueError, "LOCAL_MODEL_PROFILE_INVALID"):
            module.validate_profile(self.profile)

    def test_rejects_credentials_or_model_autostart(self):
        self.source["api_base"] = "http://user:password@127.0.0.1:11434"
        self.write()
        with self.assertRaises(ValueError):
            module.validate_profile(self.profile)
        self.source["api_base"] = "http://127.0.0.1:11434"
        self.source["enabled_by_default"] = True
        self.write()
        with self.assertRaises(ValueError):
            module.validate_profile(self.profile)

    def test_model_missing_is_not_verified(self):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass
            def read(self, *_):
                return b'{"models":[{"name":"other:4b"}]}'
        with patch.object(module.urllib.request, "urlopen", return_value=FakeResponse()):
            result = module.check_local(self.profile)
        self.assertEqual("MODEL_MISSING", result["status"])
        self.assertFalse(result["runtime_verified"])

    def test_model_present_does_not_claim_inference_success(self):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass
            def read(self, *_):
                return b'{"models":[{"name":"qwen3:4b"}]}'
        with patch.object(module.urllib.request, "urlopen", return_value=FakeResponse()):
            result = module.check_local(self.profile)
        self.assertEqual("MODEL_FOUND", result["status"])
        self.assertTrue(result["runtime_verified"])
        self.assertFalse(result["inference_verified"])


if __name__ == "__main__":
    unittest.main()
