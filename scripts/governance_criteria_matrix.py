#!/usr/bin/env python3
"""Read-only GOV-P0 criteria-to-evidence matrix. Not an acceptance authority.

Derive all six criteria from the pinned contract. Attach only independently
validated, criterion-scoped CI receipts. Explicitly preserve unresolved work.
"""
import argparse
import json
from pathlib import Path
import sys

CRITERIA = ("dashboard", "evidence", "end_to_end", "enforcement",
            "baseline_review", "impact_rollback")
PROOFS = ("governance.policy_ci", "governance.dotnet_ci")


def denial(code, reason):
    return {"code": code, "reason": reason, "status": "BLOCKED",
            "governance_acceptance": "OPEN"}


def build_matrix(contract, *, policy_receipt, dotnet_receipt, reuse_decision, pair_receipt):
    if (not isinstance(contract, dict) or contract.get("gate") != "GOV-P0"
            or contract.get("status") != "OPEN" or not isinstance(contract.get("capabilities"), list)):
        return denial("MATRIX_CONTRACT_INVALID", "GOV-P0 must remain OPEN")
    capabilities = contract["capabilities"]
    ids = [x.get("id") for x in capabilities if isinstance(x, dict)]
    if (len(ids) != 6 or set(ids) != set(CRITERIA)
            or any(x.get("state") != "OPEN" or not isinstance(x.get("proof"), str)
                   or not x["proof"].strip() for x in capabilities)):
        return denial("MATRIX_CRITERIA_INCOMPLETE", "Six unique, defined, still-open criteria required")
    for name, receipt in ((PROOFS[0], policy_receipt), (PROOFS[1], dotnet_receipt)):
        if (not isinstance(receipt, dict) or receipt.get("status") != "CHECK_OK"
                or receipt.get("criterion") != name or receipt.get("criterion_verified") is not True
                or receipt.get("reused_existing_run") is not True
                or receipt.get("new_build_or_test_invoked_by_verifier") is not False
                or receipt.get("governance_acceptance") != "OPEN"
                or not isinstance(receipt.get("historical_run_id"), int)
                or not isinstance(receipt.get("historical_checkout_sha"), str)
                or len(receipt["historical_checkout_sha"]) != 40):
            return denial("MATRIX_PROOF_INVALID", "Historical receipt is unverified or off-criterion: " + name)
    if (not isinstance(reuse_decision, dict)
            or reuse_decision.get("criterion") != PROOFS[1]
            or reuse_decision.get("status") not in ("BLOCKED", "REUSABLE")):
        return denial("MATRIX_REUSE_NOT_CHECKED", "Input-identity check for .NET proof missing")
    reuse_allowed = reuse_decision["status"] == "REUSABLE"
    if reuse_allowed:
        if (reuse_decision.get("code") != "IDENTICAL_REPOSITORY_TREE"
                or reuse_decision.get("reuse_allowed") is not True
                or reuse_decision.get("current_stage_acceptance") != "NOT_ASSESSED"):
            return denial("MATRIX_REUSE_CONTRADICTION", "Same-tree admission inconsistent")
    elif (reuse_decision.get("code") != "REUSE_INPUT_TREE_CHANGED"
          or reuse_decision.get("reuse_allowed") is not False):
        return denial("MATRIX_REUSE_CONTRADICTION", "Changed-tree denial inconsistent")
    if (not isinstance(pair_receipt, dict)
            or pair_receipt.get("status") != "PAIR_CHECK_OK"
            or pair_receipt.get("pair_verified") is not True
            or pair_receipt.get("stage_accepted") is not False
            or pair_receipt.get("governance_acceptance") != "OPEN"
            or pair_receipt.get("historical_pr_head_sha") != policy_receipt.get("historical_pr_head_sha")
            or pair_receipt.get("historical_pr_head_sha") != dotnet_receipt.get("historical_head_sha")
            or pair_receipt.get("historical_checkout_sha") != policy_receipt.get("historical_checkout_sha")
            or pair_receipt.get("historical_checkout_sha") != dotnet_receipt.get("historical_checkout_sha")
            or pair_receipt.get("run_ids") != [
                policy_receipt.get("historical_run_id"), dotnet_receipt.get("historical_run_id")]):
        return denial("MATRIX_UNBOUND_EVIDENCE_PAIR", "CI receipts are not proven to share one authentic Git checkout")
    historical_proofs = [
        {"criterion": PROOFS[0], "run_id": policy_receipt["historical_run_id"],
         "checkout_sha": policy_receipt["historical_checkout_sha"],
         "scope": "prior policy CI only", "current_revision_accepted": False},
        {"criterion": PROOFS[1], "run_id": dotnet_receipt["historical_run_id"],
         "checkout_sha": dotnet_receipt["historical_checkout_sha"],
         "scope": "prior .NET test CI only", "current_revision_accepted": False}
    ]
    return {
        "schema_version": "phantom.governance.criteria-matrix.v1",
        "status": "INVENTORIED_OPEN",
        "governance_acceptance": "OPEN", "accepted_capabilities": 0,
        "criteria_count": 6,
        "capabilities": [
            {"id": cap["id"], "acceptance_criterion": cap["proof"],
             "acceptance": "OPEN", "evidence_count_for_full_acceptance": 0,
             "missing": _missing_for(cap["id"])} for cap in capabilities
        ],
        "historical_proofs": historical_proofs,
        "historical_proofs_checked": 2,
        "historical_proofs_same_checkout_verified": True,
        "dotnet_current_revision_reuse": ("ALLOWED_FOR_IDENTICAL_TREE_ONLY" if reuse_allowed
                                          else "BLOCKED_CHANGED_INPUT_TREE"),
        "current_stage_acceptance": "NOT_ASSESSED",
        "single_lifecycle_integration_proven": False,
        "source": "versioned GOV-P0 contract and independently verified CI receipts",
    }


def _missing_for(cap):
    required = {
        "dashboard": "live GitHub Projects sync driven by verified acceptance",
        "evidence": "full stage criterion/implementation/proof coverage in one approved lifecycle",
        "end_to_end": "authorized phase execution, forced failure, durable resume and publication",
        "enforcement": "end-to-end merge admission and actionable denial/recovery proof",
        "baseline_review": "controlled amendment conflict and routine compliant-fix proof",
        "impact_rollback": "matched before/after metrics, isolated rollback and post-rollback validation",
    }
    return required[cap]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--policy-receipt", required=True)
    parser.add_argument("--dotnet-receipt", required=True)
    parser.add_argument("--reuse-decision", required=True)
    parser.add_argument("--pair-receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        inputs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in (
            args.contract, args.policy_receipt, args.dotnet_receipt, args.reuse_decision,
            args.pair_receipt)]
        report = build_matrix(inputs[0], policy_receipt=inputs[1],
                              dotnet_receipt=inputs[2], reuse_decision=inputs[3],
                              pair_receipt=inputs[4])
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report = denial("MATRIX_INPUT_UNAVAILABLE", type(exc).__name__)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("status") == "INVENTORIED_OPEN" else 1


if __name__ == "__main__":
    sys.exit(main())
