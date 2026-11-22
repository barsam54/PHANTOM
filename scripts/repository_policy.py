#!/usr/bin/env python3
"""PHANTOM repository policy gate. Stdlib only; fail closed with actionable reasons."""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ERRORS = []
ALLOWED_ROOT = {
    ".github", ".gitignore", "Directory.Build.props", "Directory.Build.targets",
    "Directory.Packages.props", "NuGet.Config", "global.json", "PHANTOM.slnx",
    "README.md", "LICENSE", "src", "tests", "benchmarks", "docs", "infra", "scripts",
}
BLOCKED_SUFFIXES = {".sqlite", ".db", ".bak", ".zip", ".tar", ".gz", ".pfx", ".pem", ".key", ".trx"}
BLOCKED_NAMES = {".env", "secrets.json"}
MAX_FILE_BYTES = 1024 * 1024

def block(code, path, reason, fix):
    ERRORS.append({"code": code, "path": path, "reason": reason, "action": fix})

def tracked_files():
    proc = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True)
    if proc.returncode:
        block("GIT_UNAVAILABLE", ".", proc.stderr.decode(errors="replace").strip(),
              "Run from a Git working tree with Git installed.")
        return []
    return [pathlib.Path(p.decode("utf-8", errors="replace")) for p in proc.stdout.split(b"\0") if p]

for rel in tracked_files():
    path = ROOT / rel
    display = rel.as_posix()
    if rel.parts[0] not in ALLOWED_ROOT:
        block("ROOT_PATH_DENIED", display, "Path is outside approved repository layout.",
              "Move into src/, tests/, docs/, infra/, scripts/, or another approved directory.")
    if rel.name.lower() in BLOCKED_NAMES or rel.suffix.lower() in BLOCKED_SUFFIXES or rel.name.startswith(".env."):
        block("ARTIFACT_DENIED", display, "Potential secret, backup, dataset, or generated result is tracked.",
              "Remove it from Git tracking; store sensitive or large runtime files outside the repository.")
    if any(part in {"bin", "obj", "TestResults", "__pycache__"} for part in rel.parts):
        block("GENERATED_FILE_DENIED", display, "Generated output is tracked.",
              "Remove generated files from Git tracking and keep them ignored.")
    if path.is_file() and path.stat().st_size > MAX_FILE_BYTES:
        block("FILE_SIZE_EXCEEDED", display, "Tracked file exceeds 1 MiB.",
              "Store large artifacts outside Git or explicitly revise the baseline through review.")

required = {
    "global.json": ('"Microsoft.Testing.Platform"', "MTP runner selection"),
    "Directory.Build.props": ("<TargetFramework>net10.0</TargetFramework>", ".NET 10 target"),
    "docs/architecture/BASELINE.md": ("### 11. Repository Layout and Storage Policy", "repository storage policy"),
}
for name, (token, purpose) in required.items():
    file = ROOT / name
    if not file.is_file():
        block("REQUIRED_FILE_MISSING", name, f"Missing {purpose}.", "Restore the required baseline file.")
    elif token not in file.read_text(encoding="utf-8"):
        block("BASELINE_CONTRACT_MISMATCH", name, f"Missing required marker for {purpose}.",
              "Restore the approved baseline setting or submit an explicit architecture change.")

report = {"gate": "repository-policy", "status": "FAIL" if ERRORS else "PASS",
          "failure_count": len(ERRORS), "failures": ERRORS}
print(json.dumps(report, indent=2, ensure_ascii=False))
sys.exit(1 if ERRORS else 0)
