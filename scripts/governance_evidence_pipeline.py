#!/usr/bin/env python3
"""Single entrypoint for PHANTOM's existing independent evidence validators.

This is a *verification adapter* for the Microsoft Agent Framework governance
workflow, NOT a second orchestrator or an acceptance authority. Provider
readback occurs in the existing artifact validators before this entrypoint.
"""
import argparse
import json
import os
from pathlib import Path
import sys

from check_governance_reuse_eligibility import assess
from governance_criteria_matrix import build_matrix
from verify_governance_artifact import fetch, SHA, REPO
from verify_governance_evidence_pair import verify_pair


def blocked(code, detail):
    return {
        "status": "BLOCKED", "code": code, "reason": detail,
        "stage": "evidence", "evidence": [],
        "action": "Repair only the failed evidence prerequisite, then rerun this pipeline.",
        "resume": "evidence", "governance_acceptance": "OPEN",
    }


def evaluate(contract, policy_receipt, dotnet_receipt, old_commit, current_commit):
    """One ordered, fail-closed evaluation. Never promotes historical CI to PASS."""
    paired = verify_pair(policy_receipt, dotnet_receipt)
    if paired.get("status") != "PAIR_CHECK_OK":
        return blocked(paired.get("code", "PAIR_UNVERIFIED"),
                       paired.get("reason", "Policy/.NET provider receipts do not match")), {}
    reuse = assess(
        criterion="governance.dotnet_ci", historical_proof=dotnet_receipt,
        historical_commit=old_commit, current_commit=current_commit)
    if reuse.get("status") not in ("BLOCKED", "REUSABLE"):
        return blocked("REUSE_STATE_UNEXPECTED", "Unrecognized input identity decision"), {}
    # Changes must deny reuse. This is a successful verification of a refusal,
    # not a successful phase acceptance or approval of an invalid input.
    if reuse["status"] == "BLOCKED" and reuse.get("code") != "REUSE_INPUT_TREE_CHANGED":
        return blocked(reuse.get("code", "REUSE_UNVERIFIED"),
                       reuse.get("reason", "Unable to verify input identity")), {}
    matrix = build_matrix(
        contract, policy_receipt=policy_receipt, dotnet_receipt=dotnet_receipt,
        reuse_decision=reuse, pair_receipt=paired)
    if matrix.get("status") != "INVENTORIED_OPEN":
        return blocked(matrix.get("code", "MATRIX_UNVERIFIED"),
                       matrix.get("reason", "Cannot map all acceptance criteria")), {}
    if (matrix.get("criteria_count") != 6 or matrix.get("accepted_capabilities") != 0
            or matrix.get("historical_proofs_same_checkout_verified") is not True):
        return blocked("MATRIX_ACCEPTANCE_INCONSISTENT", "Unexpected acceptance or incomplete criteria"), {}
    return {
        "schema_version": "phantom.governance.evidence-pipeline.v1",
        "status": "VERIFIED_SCOPE_ONLY", "stage": "evidence",
        "code": "CI_PROVENANCE_BOUND_NOT_PHASE_ACCEPTANCE",
        "evidence_pair": "PAIR_CHECK_OK",
        "reuse_decision": reuse["status"],
        "reuse_code": reuse["code"],
        "criteria_discovered": 6,
        "historical_ci_criteria_verified": 2,
        "current_phase_criteria_verified": 0,
        "current_stage_acceptance": "NOT_ASSESSED",
        "governance_acceptance": "OPEN",
        "accepted_capabilities": 0,
        "phase_evidence_verification_completed": False,
        "action": "Supply a real phase-scoped manifest and bind verified receipts to the Microsoft workflow evidence executor.",
        "resume": "evidence",
    }, {"pair": paired, "reuse": reuse, "matrix": matrix}


def main():
    p = argparse.ArgumentParser()
    for flag in ("contract", "policy-receipt", "dotnet-receipt", "repo", "current-sha", "output-dir"):
        p.add_argument("--" + flag, required=True)
    args = p.parse_args()
    directory = Path(args.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    if not REPO.fullmatch(args.repo or "") or not SHA.fullmatch(args.current_sha or ""):
        result, details = blocked("PIPELINE_REQUEST_INVALID", "Pin repository and complete SHA"), {}
    else:
        try:
            contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
            policy = json.loads(Path(args.policy_receipt).read_text(encoding="utf-8"))
            dotnet = json.loads(Path(args.dotnet_receipt).read_text(encoding="utf-8"))
            old = dotnet.get("historical_checkout_sha")
            if not isinstance(old, str) or not SHA.fullmatch(old):
                raise ValueError("PINNED_HISTORICAL_CHECKOUT_REQUIRED")
            prefix = "https://api.github.com/repos/" + args.repo + "/commits/"
            token = os.environ.get("GITHUB_TOKEN")
            previous_commit = json.loads(fetch(prefix + old, token))
            current_commit = json.loads(fetch(prefix + args.current_sha, token))
            result, details = evaluate(
                contract, policy, dotnet, previous_commit, current_commit)
        except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
            result, details = blocked("PIPELINE_READBACK_FAILED", type(exc).__name__), {}
    for name, document in (
        ("governance-evidence-pipeline.json", result),
        ("governance-evidence-pair.json", details.get("pair")),
        ("dotnet-reuse-eligibility.json", details.get("reuse")),
        ("governance-criteria-matrix.json", details.get("matrix")),
    ):
        if document is not None:
            (directory / name).write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "VERIFIED_SCOPE_ONLY" else 1


if __name__ == "__main__":
    sys.exit(main())
