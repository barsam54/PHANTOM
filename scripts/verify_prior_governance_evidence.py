#!/usr/bin/env python3
"""Cross-run evidence readback; uses official actions/download-artifact for transport.

A successful readback validates historical GOV-P0 inventory, never the
current source revision or a whole stage's acceptance.
"""
import argparse
import io
import json
import os
from pathlib import Path
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from verify_governance_artifact import (
    CONTRACT, BASELINE, MAX_ZIP, REPO, SHA, DIGEST, denial, fetch,
    inspect_archive, sha,
)

FILES = ("governance-inventory.json", "governance-phase0-ten-steps.json")


def verify_extracted(repo, run_id, expected_head, directory, *, read=fetch, token=None):
    if not REPO.fullmatch(repo or "") or not SHA.fullmatch(expected_head or "") or run_id <= 0:
        return denial("REQUEST_INVALID", "Pin repository, run id and full head SHA")
    api = "https://api.github.com/repos/" + repo
    run = json.loads(read(api + "/actions/runs/" + str(run_id), token))
    jobs = json.loads(read(api + "/actions/runs/" + str(run_id) + "/jobs?per_page=100", token))
    arts = json.loads(read(api + "/actions/runs/" + str(run_id) + "/artifacts?per_page=100", token))
    if (run.get("id") != run_id or run.get("head_sha") != expected_head or
        run.get("name") != "Repository Policy Guard" or run.get("event") != "pull_request" or
        run.get("status") != "completed" or run.get("conclusion") != "success"):
        return denial("RUN_PROVENANCE_INVALID", "Earlier run must be a completed, successful PR run")
    jobs_list = jobs.get("jobs")
    if (not isinstance(jobs_list, list) or not jobs_list or
        jobs.get("total_count", 0) > 100 or
        any(j.get("status") != "completed" or j.get("conclusion") != "success" for j in jobs_list)):
        return denial("JOBS_UNVERIFIED", "Earlier jobs not completely successful")
    entries = arts.get("artifacts", [])
    if arts.get("total_count", 0) > 100:
        return denial("ARTIFACT_PAGINATION_UNVERIFIED", "More than 100 artifacts")
    matches = [x for x in entries if x.get("name") == "governance-inventory"]
    if len(matches) != 1:
        return denial("ARTIFACT_MISSING_OR_DUPLICATE", "Expected unique artifact")
    artifact = matches[0]
    origin = artifact.get("workflow_run") or {}
    if (origin.get("id") != run_id or origin.get("head_sha") != expected_head or
        artifact.get("expired") is not False or
        not DIGEST.fullmatch(artifact.get("digest") or "") or
        not isinstance(artifact.get("id"), int) or artifact["id"] <= 0):
        return denial("ARTIFACT_IDENTITY_INVALID", "Provider artifact metadata does not match")
    directory = Path(directory)
    if not directory.is_dir():
        return denial("EVIDENCE_DIR_MISSING", "Official download action did not extract artifact")
    content = {}
    for name in FILES:
        path = directory / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_ZIP:
            return denial("EVIDENCE_CONTENT_MISSING", "Missing, symlinked or oversized " + name)
        content[name] = path.read_bytes()
    inv = json.loads(content[FILES[0]])
    checkout_sha = inv.get("commit_sha")
    if not isinstance(checkout_sha, str) or not SHA.fullmatch(checkout_sha):
        return denial("CHECKOUT_SHA_INVALID", "Unpinned checkout hash in prior artifact")
    merge = json.loads(read(api + "/commits/" + checkout_sha, token))
    parents = merge.get("parents") or []
    if (merge.get("sha") != checkout_sha or len(parents) != 2 or
        parents[1].get("sha") != expected_head):
        return denial("MERGE_LINEAGE_INVALID", "Prior merge checkout not tied to declared head")
    raw = "https://raw.githubusercontent.com/" + repo + "/" + checkout_sha + "/"
    contract = read(raw + CONTRACT, None)
    baseline = read(raw + BASELINE, None)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o600 << 16
            archive.writestr(entry, content[name])
    payload = buffer.getvalue()
    # The newly repacked ZIP is NOT the original GitHub artifact archive.
    # Authenticity of extracted files is delegated to actions/download-artifact.
    result = inspect_archive(payload, {"digest": "sha256:" + sha(payload)},
                             checkout_sha, contract, baseline)
    if result["status"] != "CHECK_OK":
        return result
    result.update({
        "historical_run_id": run_id,
        "historical_pr_head_sha": expected_head,
        "historical_checkout_sha": checkout_sha,
        "artifact_id": artifact["id"],
        "provider_artifact_sha256": artifact["digest"],
        "repacked_validation_zip_sha256": sha(payload),
        "transport": "actions/download-artifact@v4 with repository, run-id and github-token",
        "archive_digest_equality_tested_by_python": False,
        "reused_existing_run": True,
        "new_build_or_test_invoked_by_verifier": False,
        "historical_evidence_scope": "governance.policy_ci reports at original commit only",
        "current_revision_acceptance": "NOT_ASSESSED",
        "governance_acceptance": "OPEN",
    })
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--run-id", required=True, type=int)
    p.add_argument("--head-sha", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        result = verify_extracted(args.repo, args.run_id, args.head_sha,
                                  args.dir, token=os.environ.get("GITHUB_TOKEN"))
    except (OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        result = denial("PRIOR_EVIDENCE_UNREADABLE", type(exc).__name__ + ": " + str(exc))
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "CHECK_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
