#!/usr/bin/env python3
"""GitHub-attested historical .NET CI evidence verification; never stage acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from verify_governance_artifact import (
    BASELINE, CONTRACT, REPO, SHA, DIGEST, denial, fetch
)

CRITERION = "governance.dotnet_ci"
NAME = "governance-dotnet-test-evidence"
WORKFLOW = "PHANTOM .NET Build and Tests"
PROJECT = "tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj"
MAX_LOG = 4 * 1024 * 1024


def verify(repo, run_id, head_sha, directory, *, read=fetch, token=None):
    if not REPO.fullmatch(repo or "") or not SHA.fullmatch(head_sha or "") or run_id <= 0:
        return denial("INVALID_REQUEST", "Pin repository, positive run ID and full SHA")
    api = "https://api.github.com/repos/" + repo
    base = api + "/actions/runs/" + str(run_id)
    run = json.loads(read(base, token))
    jobs = json.loads(read(base + "/jobs?per_page=100", token))
    artifacts = json.loads(read(base + "/artifacts?per_page=100", token))
    if (run.get("id") != run_id or run.get("head_sha") != head_sha or
        run.get("event") != "pull_request" or run.get("name") != WORKFLOW or
        run.get("status") != "completed" or run.get("conclusion") != "success"):
        return denial("DOTNET_RUN_PROVENANCE_INVALID", "Untrusted/incomplete CI run")
    entries = jobs.get("jobs")
    if (not isinstance(entries, list) or not entries or jobs.get("total_count", 0) > 100 or
        any(j.get("conclusion") != "success" or j.get("status") != "completed"
            for j in entries)):
        return denial("DOTNET_JOBS_NOT_SUCCESSFUL", "Run has failed or missing jobs")
    steps = [step for job in entries for step in job.get("steps", [])]
    exact_tests = [s for s in steps if s.get("name") == "Run MSTest using Microsoft.Testing.Platform"]
    if len(exact_tests) != 1 or exact_tests[0].get("conclusion") != "success":
        return denial("DOTNET_TEST_EXECUTION_MISSING", "Cannot locate passing real test step")
    if artifacts.get("total_count", 0) > 100:
        return denial("DOTNET_ARTIFACT_PAGINATION", "Incomplete provider artifact pagination")
    found = [a for a in artifacts.get("artifacts", []) if a.get("name") == NAME]
    if len(found) != 1:
        return denial("DOTNET_ARTIFACT_NOT_UNIQUE", "Missing or duplicate .NET evidence artifact")
    art = found[0]
    origin = art.get("workflow_run") or {}
    if (art.get("expired") is not False or not DIGEST.fullmatch(art.get("digest") or "") or
        not isinstance(art.get("id"), int) or art["id"] <= 0 or
        origin.get("id") != run_id or origin.get("head_sha") != head_sha):
        return denial("DOTNET_ARTIFACT_PROVENANCE_INVALID", "Unverified provider artifact identity")
    directory = Path(directory)
    receipt = directory / "dotnet-ci-receipt.json"
    logpath = directory / "dotnet-tests.log"
    if (not receipt.is_file() or receipt.is_symlink() or
        not logpath.is_file() or logpath.is_symlink() or
        logpath.stat().st_size > MAX_LOG or logpath.stat().st_size == 0):
        return denial("DOTNET_ARTIFACT_CONTENT_MISSING", "Receipt or real test log missing")
    doc = json.loads(receipt.read_bytes())
    log = logpath.read_bytes()
    checkout_sha = doc.get("checkout_sha")
    if not isinstance(checkout_sha, str) or not SHA.fullmatch(checkout_sha):
        return denial("DOTNET_RECEIPT_SHA_INVALID", "Unpinned checkout in receipt")
    checkout = json.loads(read(api + "/commits/" + checkout_sha, token))
    parents = checkout.get("parents") or []
    if (checkout.get("sha") != checkout_sha or len(parents) != 2 or
        parents[1].get("sha") != head_sha):
        return denial("DOTNET_MERGE_LINEAGE_INVALID", "Receipt checkout not tied to this PR head")
    raw = "https://raw.githubusercontent.com/" + repo + "/" + checkout_sha + "/"
    baseline = read(raw + BASELINE, None)
    contract = read(raw + CONTRACT, None)
    dig = lambda data: hashlib.sha256(data).hexdigest()
    if (doc.get("schema_version") != "phantom.governance.dotnet-receipt.v1" or
        doc.get("criterion_id") != CRITERION or
        doc.get("test_project") != PROJECT or
        doc.get("test_runner") != "Microsoft.Testing.Platform" or
        doc.get("test_step_outcome") != "success" or
        doc.get("job_status_at_receipt") != "success" or
        doc.get("contract_sha256") != dig(contract) or
        doc.get("baseline_sha256") != dig(baseline) or
        doc.get("test_log_sha256") != dig(log) or doc.get("test_log_bytes") != len(log) or
        doc.get("acceptance") != "OPEN"):
        return denial("DOTNET_RECEIPT_MISMATCH", "Document or test log contradicts pinned source/CI")
    # Successful runners often report "Failed: 0"; only nonzero failures deny.
    failed_counts = re.findall(rb"(?im)^\s*Failed:\s*([0-9]+)\b", log)
    if any(int(value) > 0 for value in failed_counts):
        return denial("DOTNET_LOG_FAILURE_MARKER", "Test log reports failed tests")
    return {
        "status": "CHECK_OK", "criterion_verified": True, "criterion": CRITERION,
        "historical_run_id": run_id, "historical_head_sha": head_sha,
        "historical_checkout_sha": checkout_sha, "artifact_id": art["id"],
        "provider_archive_digest": art["digest"], "test_log_sha256": dig(log),
        "test_log_bytes": len(log), "reused_existing_run": True,
        "new_build_or_test_invoked_by_verifier": False,
        "verified_scope": "prior dotnet CI run, pinned test log, job and artifact only",
        "current_revision_acceptance": "NOT_ASSESSED", "governance_acceptance": "OPEN"
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--head-sha", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    try:
        result = verify(a.repo, a.run_id, a.head_sha, a.dir,
                        token=os.environ.get("GITHUB_TOKEN"))
    except (OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        result = denial("DOTNET_EVIDENCE_READ_FAILED", type(exc).__name__ + ": " + str(exc))
    Path(a.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "CHECK_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
