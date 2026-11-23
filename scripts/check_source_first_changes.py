#!/usr/bin/env python3
"""Fail-closed source-first PR change admission. Python standard library only.

This verifies decision-to-PR path coverage and official citation shape.
It does NOT certify factual correctness of vendor documentation or approve code.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RECORD = "docs/architecture/SOURCE-FIRST-DECISION.json"
CONTRACT = "docs/architecture/GOVERNANCE-CONTRACT.json"
HEX_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def denial(code, reason, action, evidence=RECORD):
    return {"code": code, "stage": "source_first", "reason": reason,
            "evidence": [evidence], "action": action, "resume": "source_first"}


def changed_files(root, base_sha):
    if not HEX_SHA.fullmatch(base_sha or ""):
        raise ValueError("GOV_BASE_SHA_INVALID")
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", "-z",
         "--diff-filter=ACMR", base_sha, "HEAD", "--"],
        capture_output=True, check=True)
    return sorted({
        p.decode("utf-8") for p in result.stdout.split(b"\0") if p
    })


def evaluate(root, paths, *, contract_file=CONTRACT, decision_file=RECORD):
    """Fail closed for every changed file. No trust in mere presence of URLs."""
    root = Path(root)
    problems = []
    try:
        contract = json.loads((root / contract_file).read_text(encoding="utf-8"))
        decision = json.loads((root / decision_file).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [denial("GOV_SOURCE_RECORD_UNREADABLE", str(exc),
                       "Restore valid, versioned source-first contract and decision.")]
    source = contract.get("source_first")
    if not isinstance(source, dict) or source.get("decision_record") != decision_file:
        return [denial("GOV_SOURCE_CONTRACT_MISSING",
                       "Source-first record is not bound to the baseline contract.",
                       "Restore the reviewed contract.")]
    scope = decision.get("scope")
    if (not isinstance(scope, list) or not scope or
        any(not isinstance(p, str) or not p or
            p.startswith("/") or "\\" in p or
            ".." in Path(p).parts for p in scope) or
        len(scope) != len(set(scope))):
        problems.append(denial("GOV_SOURCE_SCOPE_INVALID",
                               "Source decision must list exact, unique repository paths.",
                               "List each reviewed changed file path explicitly."))
        scope_set = set()
    else:
        scope_set = set(scope)
    changed = set(paths)
    if not changed:
        problems.append(denial("GOV_EMPTY_CHANGESET",
                               "No candidate changes supplied; cannot prove PR scope.",
                               "Supply the base SHA and validate the PR diff."))
    for path in sorted(changed - scope_set):
        problems.append(denial("GOV_SOURCE_CHANGE_UNREVIEWED",
                               f"File has no recorded source-first decision: {path}",
                               "Review official sources and update the versioned decision scope.",
                               path))
    for path in sorted(scope_set - changed):
        problems.append(denial("GOV_SOURCE_SCOPE_STALE",
                               f"Decision covers a file not changed by this PR: {path}",
                               "Refresh the decision against the exact current PR diff.",
                               path))
    official_sources = decision.get("official_sources", [])
    approved_hosts = set(source.get("official_hosts", []))
    if not isinstance(official_sources, list) or not official_sources:
        problems.append(denial("GOV_OFFICIAL_SOURCE_MISSING",
                               "Source-first decision must cite primary vendor documentation.",
                               "Consult official documentation and record applicability and tests."))
    else:
        for i, item in enumerate(official_sources):
            if not isinstance(item, dict):
                problems.append(denial("GOV_OFFICIAL_SOURCE_INVALID",
                                       "Source entry must be an object.",
                                       "Record an official HTTPS source."))
                continue
            link = item.get("url", "")
            parsed = urlparse(link) if isinstance(link, str) else None
            if (not parsed or parsed.scheme != "https" or
                parsed.hostname not in approved_hosts or parsed.username or
                parsed.password or parsed.fragment or any(
                    not isinstance(item.get(k), str) or not item[k].strip()
                    for k in ("provider", "url", "applies_to",
                              "reviewed_version", "verification"))):
                problems.append(denial("GOV_OFFICIAL_SOURCE_INVALID",
                                       f"Official source {i} has invalid host or review evidence.",
                                       "Review authoritative HTTPS documentation and applicability."))
    if decision.get("status") != "EVIDENCE_REVIEWED":
        problems.append(denial("GOV_SOURCE_REVIEW_NOT_CONFIRMED",
                               "Proposed or unreviewed decision cannot pass preflight.",
                               "Complete review and record version-specific test evidence."))
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-sha", required=True)
    opts = parser.parse_args()
    try:
        paths = changed_files(ROOT, opts.base_sha)
        problems = evaluate(ROOT, paths)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        problems = [denial("GOV_SOURCE_DIFF_UNAVAILABLE", str(exc),
                           "Fetch the PR base commit and rerun the source-first gate.")]
        paths = []
    print(json.dumps({"status": "BLOCKED" if problems else "CHECK_OK",
                      "changed_files": paths, "denials": problems}, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
