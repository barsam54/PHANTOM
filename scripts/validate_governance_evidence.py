#!/usr/bin/env python3
"""Independent GitHub Actions receipt verification, not GOV-P0 acceptance.

Read GitHub's REST API (not a claimant-supplied manifest) for the completed
workflow, its jobs and artifact metadata. Artifact digest is metadata only:
this does NOT inspect the content of an artifact ZIP or prove stage acceptance.
"""
import argparse
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
CRITERIA = {
    "governance.policy_ci": ("Repository Policy Guard", "governance-inventory"),
    "governance.dotnet_ci": ("PHANTOM .NET Build and Tests", "governance-proposal-handoff"),
}


def denial(code, reason):
    return {"status": "BLOCKED", "code": code, "reason": reason,
            "verified": False, "governance_acceptance": "OPEN"}


def verify(run, jobs, artifacts, *, expected_sha, run_id, criterion):
    """Check provider-returned receipts against an explicitly pinned revision."""
    if criterion not in CRITERIA:
        return denial("UNKNOWN_CRITERION", "Unrecognized acceptance proof criterion")
    if not SHA.fullmatch(expected_sha or ""):
        return denial("INVALID_EXPECTED_SHA", "Commit must be pinned to a full SHA")
    workflow, name = CRITERIA[criterion]
    if (run.get("id") != run_id or run.get("head_sha") != expected_sha or
        run.get("name") != workflow or run.get("event") != "pull_request"):
        return denial("RUN_IDENTITY_MISMATCH", "Wrong run, revision, workflow or event")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return denial("RUN_NOT_SUCCESSFUL", "Workflow run was not completed successfully")
    entries = jobs.get("jobs")
    if (not isinstance(entries, list) or not entries or
        any(j.get("status") != "completed" or j.get("conclusion") != "success"
            for j in entries)):
        return denial("JOB_NOT_SUCCESSFUL", "All workflow jobs must complete successfully")
    candidates = [a for a in artifacts.get("artifacts", []) if a.get("name") == name]
    if len(candidates) != 1:
        return denial("ARTIFACT_MISSING_OR_DUPLICATE", "Required named artifact not unique")
    a = candidates[0]
    provenance = a.get("workflow_run") or {}
    if (a.get("expired") is not False or
        not isinstance(a.get("size_in_bytes"), int) or a["size_in_bytes"] <= 0 or
        not DIGEST.fullmatch(a.get("digest") or "") or
        provenance.get("id") != run_id or provenance.get("head_sha") != expected_sha):
        return denial("ARTIFACT_PROVENANCE_INVALID", "Artifact metadata or run binding invalid")
    return {
        "status": "CHECK_OK", "criterion": criterion, "run_id": run_id,
        "code_sha": expected_sha, "workflow": workflow,
        "jobs_checked": len(entries), "artifact_id": a.get("id"),
        "artifact_name": name, "artifact_archive_digest": a["digest"],
        "artifact_size_bytes": a["size_in_bytes"],
        "artifact_contents_readback": False,
        "artifact_criterion_coverage_verified": False,
        "reused_as_stage_acceptance": False,
        "verified": True, "verified_scope": "provider_run_jobs_and_artifact_metadata_only",
        "governance_acceptance": "OPEN",
    }


def get_json(url, token):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "PHANTOM-governance-evidence-validator",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.load(response)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--expected-sha", required=True)
    ap.add_argument("--criterion", choices=sorted(CRITERIA), required=True)
    ap.add_argument("--json-out")
    args = ap.parse_args()
    if not REPO.fullmatch(args.repo or "") or args.run_id <= 0:
        result = denial("INVALID_REQUEST", "Invalid repository or run identifier")
    else:
        base = "https://api.github.com/repos/" + args.repo + "/actions/runs/" + str(args.run_id)
        try:
            token = os.environ.get("GITHUB_TOKEN")
            run = get_json(base, token)
            jobs = get_json(base + "/jobs?per_page=100", token)
            artifacts = get_json(base + "/artifacts?per_page=100", token)
            if jobs.get("total_count", 0) > 100 or artifacts.get("total_count", 0) > 100:
                result = denial("PAGINATION_UNVERIFIED", "Run contains more than 100 jobs/artifacts")
            else:
                result = verify(run, jobs, artifacts, expected_sha=args.expected_sha,
                                run_id=args.run_id, criterion=args.criterion)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
            result = denial("PROVIDER_READ_FAILED", type(exc).__name__ + ": " + str(exc))
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        from pathlib import Path
        Path(args.json_out).write_text(output, encoding="utf-8")
    print(output)
    return 0 if result["status"] == "CHECK_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
