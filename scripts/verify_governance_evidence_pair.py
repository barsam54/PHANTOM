#!/usr/bin/env python3
"""Independent *pair binding* of two provider-validated CI evidence receipts.

Binding a pair is not accepting a whole GOV-P0 stage. Every source claim is
limited to the historical exact checkout and its original acceptance criteria.
"""
import argparse
import json
from pathlib import Path
import re
import sys

SHA = re.compile(r"^[0-9a-f]{40}$")


def blocked(code, reason):
    return {"status": "BLOCKED", "code": code, "reason": reason,
            "pair_verified": False, "governance_acceptance": "OPEN"}


def verify_pair(policy, dotnet):
    if not isinstance(policy, dict) or not isinstance(dotnet, dict):
        return blocked("PAIR_INPUT_INVALID", "Two independently verified receipt objects required")
    for receipt, criterion, pr_sha_key in [
        (policy, "governance.policy_ci", "historical_pr_head_sha"),
        (dotnet, "governance.dotnet_ci", "historical_head_sha")
    ]:
        if (receipt.get("status") != "CHECK_OK"
            or receipt.get("criterion") != criterion
            or receipt.get("criterion_verified") is not True
            or receipt.get("reused_existing_run") is not True
            or receipt.get("new_build_or_test_invoked_by_verifier") is not False
            or receipt.get("governance_acceptance") != "OPEN"
            or not isinstance(receipt.get("historical_run_id"), int)
            or receipt["historical_run_id"] <= 0
            or not isinstance(receipt.get(pr_sha_key), str)
            or not SHA.fullmatch(receipt[pr_sha_key])
            or not isinstance(receipt.get("historical_checkout_sha"), str)
            or not SHA.fullmatch(receipt["historical_checkout_sha"])):
            return blocked("PAIR_RECEIPT_UNVERIFIED", "Prior CI proof missing or off criterion: " + criterion)
    if policy["historical_run_id"] == dotnet["historical_run_id"]:
        return blocked("PAIR_RUN_ID_COLLISION", "Distinct workflow runs are mandatory")
    if policy["historical_pr_head_sha"] != dotnet["historical_head_sha"]:
        return blocked("PAIR_HEAD_SHA_MISMATCH", "Policy and .NET evidence refer to different PR head commits")
    if policy["historical_checkout_sha"] != dotnet["historical_checkout_sha"]:
        return blocked("PAIR_CHECKOUT_SHA_MISMATCH", "GitHub PR merge checkouts differ; source inputs not proven identical")
    return {
        "status": "PAIR_CHECK_OK", "code": "IDENTICAL_PR_HEAD_AND_CHECKOUT",
        "pair_verified": True, "historical_pr_head_sha": policy["historical_pr_head_sha"],
        "historical_checkout_sha": policy["historical_checkout_sha"],
        "criteria_verified": ["governance.policy_ci", "governance.dotnet_ci"],
        "run_ids": [policy["historical_run_id"], dotnet["historical_run_id"]],
        "new_tests_executed_by_pairing": False, "scope": "two historical CI criteria at identical Git checkout only",
        "stage_accepted": False, "governance_acceptance": "OPEN",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--policy-receipt", required=True)
    p.add_argument("--dotnet-receipt", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    try:
        policy = json.loads(Path(a.policy_receipt).read_text(encoding="utf-8"))
        dotnet = json.loads(Path(a.dotnet_receipt).read_text(encoding="utf-8"))
        result = verify_pair(policy, dotnet)
    except (OSError, ValueError, TypeError) as exc:
        result = blocked("PAIR_READ_FAILED", type(exc).__name__)
    Path(a.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "PAIR_CHECK_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
