#!/usr/bin/env python3
"""Fail-closed eligibility for reusing historical CI evidence on a new revision.

For now, relevant inputs are conservatively defined as the entire Git tree.
Two distinct commits MAY share that exact tree; any tree change is denied.
Historical receipt verification is still prerequisite, never stage acceptance.
"""
import argparse
import json
import os
import re
import sys

from verify_governance_artifact import SHA, REPO, denial, fetch

CRITERIA = {"governance.policy_ci", "governance.dotnet_ci"}


def assess(*, criterion, historical_proof, historical_commit, current_commit):
    if criterion not in CRITERIA:
        return denial("REUSE_UNKNOWN_CRITERION", "Only registered CI evidence criteria are eligible")
    if (not isinstance(historical_proof, dict) or
        historical_proof.get("status") != "CHECK_OK" or
        historical_proof.get("criterion_verified") is not True or
        historical_proof.get("criterion") != criterion or
        historical_proof.get("reused_existing_run") is not True or
        historical_proof.get("new_build_or_test_invoked_by_verifier") is not False or
        historical_proof.get("governance_acceptance") != "OPEN"):
        return denial("REUSE_PROOF_UNVERIFIED", "Prior scoped proof must be provider-verified")
    old = historical_proof.get("historical_checkout_sha")
    current_sha = current_commit.get("sha") if isinstance(current_commit, dict) else None
    if (not isinstance(old, str) or not SHA.fullmatch(old) or
        not isinstance(current_sha, str) or not SHA.fullmatch(current_sha) or
        not isinstance(historical_commit, dict) or historical_commit.get("sha") != old):
        return denial("REUSE_REVISION_NOT_ATTESTED", "Pinned original/current commits not verified")
    old_tree = (historical_commit.get("commit") or {}).get("tree", {}).get("sha")
    current_tree = (current_commit.get("commit") or {}).get("tree", {}).get("sha")
    if (not isinstance(old_tree, str) or not SHA.fullmatch(old_tree) or
        not isinstance(current_tree, str) or not SHA.fullmatch(current_tree)):
        return denial("REUSE_TREE_NOT_ATTESTED", "Original/current Git tree unavailable")
    if old_tree != current_tree:
        return {
            **denial("REUSE_INPUT_TREE_CHANGED", "At least one repository input changed; rerun CI"),
            "historical_tree": old_tree, "current_tree": current_tree,
            "criterion": criterion, "reuse_allowed": False,
            "required_action": "Run this criterion against the current commit; do not inherit old PASS",
        }
    return {
        "status": "REUSABLE", "code": "IDENTICAL_REPOSITORY_TREE",
        "criterion": criterion, "historical_sha": old, "current_sha": current_sha,
        "identical_input_tree": old_tree, "reuse_allowed": True,
        "scope": "identical complete repository tree, historical criterion only",
        "new_build_or_test_invoked": False, "current_stage_acceptance": "NOT_ASSESSED",
        "governance_acceptance": "OPEN",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--historical-report", required=True)
    ap.add_argument("--current-sha", required=True)
    ap.add_argument("--criterion", choices=sorted(CRITERIA), required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    if not REPO.fullmatch(args.repo or "") or not SHA.fullmatch(args.current_sha or ""):
        result = denial("REUSE_INVALID_REQUEST", "Expected a repository and a full commit SHA")
    else:
        try:
            with open(args.historical_report, encoding="utf-8") as f:
                proof = json.load(f)
            old_sha = proof.get("historical_checkout_sha")
            if not isinstance(old_sha, str) or not SHA.fullmatch(old_sha):
                result = denial("REUSE_PROOF_UNVERIFIED", "No original checkout SHA in prior report")
            else:
                api = "https://api.github.com/repos/" + args.repo + "/commits/"
                token = os.environ.get("GITHUB_TOKEN")
                past = json.loads(fetch(api + old_sha, token))
                current = json.loads(fetch(api + args.current_sha, token))
                result = assess(criterion=args.criterion, historical_proof=proof,
                                historical_commit=past, current_commit=current)
        except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
            result = denial("REUSE_LOOKUP_FAILED", type(exc).__name__)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    # Changed inputs are an expected denial, not a CI error, but never allow reuse.
    return 0 if result.get("status") in ("REUSABLE", "BLOCKED") else 1


if __name__ == "__main__":
    sys.exit(main())
