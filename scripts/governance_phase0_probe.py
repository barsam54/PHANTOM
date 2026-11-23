#!/usr/bin/env python3
"""GOV-P0 10-step integration-readiness probe. No mutations or false acceptance."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = "docs/architecture/GOVERNANCE-CONTRACT.json"
STEPS = (
    "discover", "baseline_review", "dependencies", "plan",
    "authorized_execute", "build_and_tests", "evidence",
    "acceptance", "publish", "checkpoint",
)
DENIAL_FIELDS = ("code", "stage", "reason", "evidence", "action", "resume")


def git_sha(root):
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result(step, state, code, reason, action, evidence, resume):
    return {
        "step": step, "state": state, "code": code, "stage": "GOV-P0",
        "reason": reason, "evidence": evidence, "action": action, "resume": resume,
    }


def run_probe(root=ROOT):
    sha = git_sha(root)
    stages = []
    contract_file = root / CONTRACT_FILE
    if not contract_file.is_file():
        raise ValueError("GOV_CONTRACT_MISSING: " + CONTRACT_FILE)
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    if contract.get("phase_steps") != list(STEPS):
        raise ValueError("GOV_STAGE_CONTRACT_MISMATCH: ordered 10-step contract unavailable")
    if contract.get("status") != "OPEN":
        raise ValueError("GOV_PREMATURE_ACCEPTANCE: contract must remain OPEN")
    if len(contract.get("capabilities", [])) != 6:
        raise ValueError("GOV_CAPABILITY_MISMATCH: six capabilities required")

    # Each recorded step runs a concrete check or explicitly identifies the
    # unavailable execution dependency. A missing capability cannot become PASS.
    evidence_root = root / "docs/evidence"
    evidence_files = list(evidence_root.glob("*.md")) if evidence_root.is_dir() else []
    stages.append(result(STEPS[0], "CHECK_OK", "DISCOVERY_COMPLETED",
        "Read pinned Git HEAD, contract and existing evidence-file inventory. Historical evidence NOT verified.",
        "Validate provenance and scope before accepting any historical result.",
        [CONTRACT_FILE, "docs/evidence/"], "baseline_review"))
    baseline_path = root / contract.get("baseline", "")
    if baseline_path.is_file() and "Six simultaneous, complementary capabilities" in baseline_path.read_text(encoding="utf-8"):
        stages.append(result(STEPS[1], "CHECK_OK", "BASELINE_REVISION_IDENTIFIED",
            "Versioned six-capability P0 clause found. This does not prove that the baseline is scientifically correct.",
            "Investigate a specific conflict with official Microsoft docs and a reproducible case before amendment.",
            [contract["baseline"]], "dependencies"))
    else:
        stages.append(result(STEPS[1], "BLOCKED", "BASELINE_MISSING_OR_MISMATCH",
            "Versioned six-capability P0 baseline clause not found.",
            "Restore the correct baseline revision or submit an evidenced amendment.",
            [contract.get("baseline", CONTRACT_FILE)], "baseline_review"))

    af_proj = root / "src/Phantom.AgentFramework/Phantom.AgentFramework.csproj"
    if af_proj.is_file() and "Microsoft.Agents.AI.Workflows" in af_proj.read_text(encoding="utf-8"):
        stages.append(result(STEPS[2], "CHECK_OK", "FRAMEWORK_DEPENDENCY_DECLARED",
            "C# Microsoft Agent Framework dependency exists. No governance runner or end-to-end dependency evaluation proven.",
            "Verify pinned C# APIs, worker permissions, durable checkpoint store, and stage-specific dependency graph.",
            ["src/Phantom.AgentFramework/Phantom.AgentFramework.csproj"], "plan"))
    else:
        stages.append(result(STEPS[2], "BLOCKED", "FRAMEWORK_DEPENDENCY_MISSING",
            "C# Microsoft Agent Framework package reference not found.",
            "Resolve approved package reference against official Microsoft docs.",
            ["src/Phantom.AgentFramework/Phantom.AgentFramework.csproj"], "dependencies"))

    stages.append(result(STEPS[3], "CHECK_OK", "PLAN_CONTRACT_READ",
        "All ten ordered stage names exist in the approved contract; this is NOT an executed implementation plan.",
        "Generate a real authorized plan from evidence and dependencies, with rollback point and predeclared metrics.",
        [CONTRACT_FILE], "authorized_execute"))

    stages.append(result(STEPS[4], "NOT_IMPLEMENTED", "AUTHORIZED_WORKER_ABSENT",
        "No verified end-to-end governance coding worker with bounded scope has been connected to this probe.",
        "Implement and integration-test a least-privilege Microsoft Agent Framework governance worker before enabling edits.",
        ["docs/architecture/GOVERNANCE-CONTROLLER.md"], "authorized_execute"))

    stages.append(result(STEPS[5], "NOT_EXECUTED", "STAGE_BUILD_TEST_NOT_EXECUTED",
        "This read-only probe does not run stage-specific .NET build, regression, or before/after evaluation; other CI jobs are separate.",
        "Link exact-SHA CI results and run stage-specific positive/negative/regression and impact checks.",
        [".github/workflows/dotnet-build-test.yml"], "build_and_tests"))

    stages.append(result(STEPS[6], "CHECK_OK", "EVIDENCE_INVENTORY_ONLY",
        "Listed historical evidence files without checking their test runs, provenance, digest, or acceptance scope.",
        "Verify source SHA, criterion and test results; create an attested stage evidence manifest.",
        ["docs/evidence/"], "evidence"))

    stages.append(result(STEPS[7], "BLOCKED", "ACCEPTANCE_UNPROVEN",
        "No independently verified change-impact, complete stage test coverage, rollback and replay proof.",
        "Do not accept; first execute missing proof and a negative acceptance test.",
        ["docs/architecture/GOVERNANCE-CONTRACT.json"], "acceptance"))

    stages.append(result(STEPS[8], "NOT_IMPLEMENTED", "AUTOMATIC_PUBLICATION_NOT_PROVEN",
        "No verified stage-specific automatic commit/PR and GitHub Projects sync has run in this probe.",
        "Implement idempotent publication and verify GitHub Project matches accepted manifest.",
        [".github/workflows/repository-policy.yml"], "publish"))

    stages.append(result(STEPS[9], "NOT_IMPLEMENTED", "DURABLE_RESUME_UNPROVEN",
        "No durable governance checkpoint and forced restart/resume test; research SML checkpoints are separate.",
        "Persist governance execution ID/checkpoint and prove restart without duplicated external side effects.",
        ["docs/architecture/GOVERNANCE-CONTROLLER.md"], "checkpoint"))

    return {
        "schema_version": "phantom.gov-p0.phase0-ten-step-probe.v1",
        "kind": "READ_ONLY_INTEGRATION_READINESS_PROBE",
        "sha": sha,
        "baseline_sha256": sha256(baseline_path) if baseline_path.is_file() else None,
        "contract_sha256": sha256(contract_file),
        "historical_evidence_files_discovered": len(evidence_files),
        "historical_evidence_verified": False,
        "phase": "GOV-P0",
        "overall_acceptance": "OPEN",
        "steps": stages,
        "step_count": len(stages),
        "all_steps_executed": False,
        "runner_mutated_repository": False,
    }


def summary(data):
    lines = ["# GOV-P0 — Ten-step phase execution readiness probe", "",
        "**Acceptance: OPEN. Diagnostic only; no end-to-end phase execution.**",
        "", "| # | Step | Result | Reason / remedy |", "|---:|---|---|---|"]
    for i, row in enumerate(data["steps"], 1):
        short = row["reason"] + " Action: " + row["action"]
        lines.append(f"| {i} | {row['step']} | {row['state']} | {short.replace('|', '/')} |")
    lines.extend(["", "Historical evidence files found: " +
                  str(data["historical_evidence_files_discovered"]) +
                  "; independently verified: NO.", "",
                  "Rollback execution: NOT TESTED. GitHub Projects sync: NOT TESTED.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out")
    parser.add_argument("--summary-out")
    args = parser.parse_args()
    try:
        data = run_probe()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, TypeError) as exc:
        denied = {"status": "BLOCKED", "denial": {
            "code": "GOV_PHASE0_PREFLIGHT_FAILED", "stage": "GOV-P0",
            "reason": str(exc), "evidence": [CONTRACT_FILE],
            "action": "Correct the failing contract or repo prerequisite before rerunning",
            "resume": "discover"}}
        print(json.dumps(denied, indent=2))
        return 2
    for filename, content in (
        (args.json_out, json.dumps(data, ensure_ascii=False, indent=2) + "\n"),
        (args.summary_out, summary(data))):
        if filename:
            path = Path(filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    # Successful diagnostic does NOT signal GOV-P0 acceptance.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
