#!/usr/bin/env python3
"""PHANTOM repository layout policy guard. Python standard library only."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {
    ".gitignore", ".gitattributes", ".editorconfig",
    "global.json", "Directory.Build.props", "Directory.Build.targets",
    "Directory.Packages.props", "NuGet.Config", "README.md",
    "LICENSE", "LICENSE.md", "PHANTOM.slnx",
}
ALLOWED_ROOT_DIRS = {
    "src", "tests", "benchmarks", "docs", "infra", "scripts", ".github",
}
BLOCKED_COMPONENTS = {"bin", "obj", "TestResults", "__pycache__", ".vs", ".idea"}
BLOCKED_SUFFIXES = {".sqlite", ".db", ".bak", ".backup", ".pfx", ".pem", ".key", ".trx"}
BLOCKED_NAMES = {".env", "secrets.json", "appsettings.Development.json"}
BLOCKED_PREFIXES = ("artifacts/", "data/", "logs/", "backups/", "backup/")
MAX_EVIDENCE_BYTES = 256 * 1024


def tracked_files():
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip())
    return [p.decode("utf-8", errors="replace") for p in proc.stdout.split(b"\0") if p]


def check_path(path):
    problems = []
    parts = Path(path).parts
    if not parts:
        return problems
    if len(parts) == 1:
        if path not in ALLOWED_ROOT_FILES:
            problems.append(("ROOT_FILE_NOT_ALLOWED", "Move this file into an approved directory or explicitly amend the baseline."))
    elif parts[0] not in ALLOWED_ROOT_DIRS:
        problems.append(("ROOT_DIRECTORY_NOT_ALLOWED", f"Directory '{parts[0]}' is not in the approved layout."))
    if any(p in BLOCKED_COMPONENTS for p in parts):
        problems.append(("GENERATED_OUTPUT_TRACKED", "Generated output must not be committed."))
    if path.startswith(BLOCKED_PREFIXES):
        problems.append(("EXTERNAL_STORAGE_REQUIRED", "Runtime artifacts, datasets, and backups belong outside the repository."))
    name = parts[-1]
    if name in BLOCKED_NAMES or name.startswith(".env.") or Path(name).suffix.lower() in BLOCKED_SUFFIXES:
        problems.append(("SENSITIVE_OR_BINARY_ARTIFACT", "This file type is prohibited from version control."))
    if path.startswith("docs/evidence/"):
        target = ROOT / path
        if target.is_file() and target.stat().st_size > MAX_EVIDENCE_BYTES:
            problems.append(("EVIDENCE_TOO_LARGE", "Evidence files must be at most 256 KiB; store large artifacts externally."))
    return problems


def main():
    try:
        paths = tracked_files()
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "reason": "GIT_INDEX_UNAVAILABLE", "details": str(exc)}, ensure_ascii=False))
        return 2
    violations = [
        {"path": path, "code": code, "reason": reason}
        for path in paths for code, reason in check_path(path)
    ]
    report = {"status": "FAIL" if violations else "PASS", "checked_files": len(paths), "violations": violations}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if violations:
        print("POLICY GUARD FAILED: see path, code and reason above.", file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
