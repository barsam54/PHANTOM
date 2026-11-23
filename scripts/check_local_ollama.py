#!/usr/bin/env python3
"""Check optional, loopback-only Ollama profile without downloading models.

Local-only preflight. Never sends project code or prompts to an LLM.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "infra/local-models/ollama-qwen3-4b.json"


def validate_profile(path=PROFILE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    url = urlparse(data.get("api_base", ""))
    if (data.get("provider") != "ollama" or data.get("model") != "qwen3:4b"
            or data.get("enabled_by_default") is not False
            or data.get("model_artifact_in_git") is not False
            or url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1"}
            or url.port != 11434 or url.username or url.password
            or url.path not in {"", "/"} or url.query or url.fragment):
        raise ValueError("LOCAL_MODEL_PROFILE_INVALID: only optional localhost Ollama qwen3:4b is permitted")
    return data


def check_local(path=PROFILE, timeout=3):
    data = validate_profile(path)
    url = data["api_base"].rstrip("/") + "/api/tags"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read(1024 * 1024).decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError) as exc:
        return {"status": "UNAVAILABLE", "model": data["model"],
                "runtime_verified": False, "reason": str(exc)}
    models = payload.get("models", [])
    installed = any(isinstance(m, dict) and
                    (m.get("name") == data["model"] or m.get("model") == data["model"])
                    for m in models) if isinstance(models, list) else False
    return {"status": "MODEL_FOUND" if installed else "MODEL_MISSING",
            "model": data["model"], "runtime_verified": installed,
            "inference_verified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-local", action="store_true",
                        help="Explicitly probe the local Ollama model listing; no inference")
    args = parser.parse_args()
    try:
        report = check_local() if args.check_local else {
            "status": "PROFILE_VALID", "runtime_verified": False,
            "inference_verified": False, "model": validate_profile()["model"]}
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "INVALID", "reason": str(exc)}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"PROFILE_VALID", "MODEL_FOUND"} else 1


if __name__ == "__main__":
    sys.exit(main())
