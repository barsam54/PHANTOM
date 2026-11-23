#!/usr/bin/env python3
"""Read-only PHANTOM governance inventory; never self-certifies PASS."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path("docs/architecture/GOVERNANCE-CONTRACT.json")
GATES = ("SML-01", "SML-02", "SML-03", "SML-04", "SML-05", "SML-06")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision(root):
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True
    ).stdout.strip()


def inventory(root=ROOT):
    contract_path = root / CONTRACT_PATH
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("gate") != "GOV-P0":
        raise ValueError("GOV_CONTRACT_INVALID: gate must be GOV-P0")
    if contract.get("status") != "OPEN":
        raise ValueError("GOV_PREMATURE_ACCEPTANCE: full integration proof not recorded")
    evidence_dir = root / "docs/evidence"
    evidence_files = sorted(evidence_dir.glob("*.md")) if evidence_dir.is_dir() else []
    hints = {
        gate: [p.relative_to(root).as_posix() for p in evidence_files
               if gate.lower().replace("-", "") in p.stem.lower().replace("-", "")]
        for gate in GATES
    }
    return {
        "schema_version": "phantom.governance.inventory.v1",
        "kind": "READ_ONLY_DISCOVERY_NOT_ACCEPTANCE",
        "commit_sha": git_revision(root),
        "contract_path": CONTRACT_PATH.as_posix(),
        "contract_digest_sha256": digest(contract_path),
        "baseline_digest_sha256": digest(root / contract["baseline"]),
        "gate": "GOV-P0", "decision": "OPEN",
        "capabilities": [
            {"id": cap["id"], "contract_state": cap["state"],
             "verified": False, "next_proof": cap["proof"]}
            for cap in contract["capabilities"]
        ],
        "historical_evidence_files_found": len(evidence_files),
        "evidence_integrity_inventory": [
            {"path": p.relative_to(root).as_posix(),
             "sha256": digest(p),
             "bytes": p.stat().st_size,
             "verified": False,
             "reason": "File integrity fingerprint only; execution provenance is not verified"}
            for p in evidence_files
        ],
        "stage_filename_hints_unverified": hints,
        "historical_evidence_verified": False,
        "dashboard": {"type": "GitHub Actions step summary",
                      "is_acceptance_authority": False, "projects_synced": False},
        "merge_barrier_history": {
            "observation": "NEGATIVE_REQUIRED_CHECK_BLOCKED",
            "evidence": "docs/evidence/2026-11-23-required-check-negative-pr.md",
            "test_pr": 2,
            "policy_run": 45097741706,
            "current_ruleset_revalidated": False,
            "direct_push_rejection_tested": False,
            "verified": False,
            "reason": "Historical GitHub API observation only; not live ruleset verification or full GOV-P0 acceptance"
        },
        "remaining": ["durable governance phase execution", "evidence provenance and acceptance",
                      "bounded authorized worker", "forced failure/resume",
                      "automatic PR publication", "GitHub Projects synchronization",
                      "periodic ruleset readback and untested direct-push denial"]
    }


def markdown(report):
    """GitHub Actions native dashboard. Status is derived only from contract."""
    capabilities = report["capabilities"]
    completed = sum(item["verified"] and item["contract_state"] == "PASS"
                    for item in capabilities)
    total = len(capabilities)
    pct = round(100 * completed / total) if total else 0
    labels = {
        "dashboard": "1. Dashboard",
        "evidence": "2. Evidence",
        "end_to_end": "3. End-to-end execution",
        "enforcement": "4. Mandatory enforcement",
        "baseline_review": "5. Baseline review",
        "impact_rollback": "6. Impact / rollback",
    }
    lines = [
        "# PHANTOM | Governance P0 dashboard",
        "",
        "> **ACCEPTANCE: OPEN**. Read-only projection of the versioned contract.",
        "> A green CI run is not acceptance of an unverified capability.",
        "",
        "### Verified capability acceptance: " + str(completed) +
        " / " + str(total) + " (" + str(pct) + "%)",
        "",
        "`" + ("█" * completed) + ("░" * (total - completed)) + "`",
        "",
        "| Capability | Decision | Verified | Next acceptance proof |",
        "|---|---|---|---|",
    ]
    for item in capabilities:
        state = item["contract_state"]
        verified = item["verified"] and state == "PASS"
        label = labels.get(item["id"], item["id"])
        lines.append("| " + label + " | **" + state + "** | " +
                     ("YES" if verified else "NO") + " | " +
                     item["next_proof"].replace("|", "/") + " |")
    lines.extend([
        "",
        "### Execution position",
        "",
        "- Revision: `" + report["commit_sha"] + "`",
        "- Contract: `" + report["contract_path"] + "`",
        "- Contract SHA-256: `" + report["contract_digest_sha256"] + "`",
        "- Baseline SHA-256: `" + report["baseline_digest_sha256"] + "`",
        "- Historical evidence files found: **" +
            str(report["historical_evidence_files_found"]) +
            "**; independently verified by this job: **NO**.",
        "- GitHub Projects synchronized: **NO**.",
        "",
        "### Execution chain (not yet accepted)",
        "",
        "`discover → baseline_review → dependencies → plan → authorized_execute → build_and_tests → evidence → acceptance → publish → checkpoint`",
        "",
        "### Verified and unverified enforcement",
        "",
    ])
    barrier = report["merge_barrier_history"]
    lines.extend([
        "- Historical negative check: test [PR #" + str(barrier["test_pr"]) +
        "](https://github.com/barsam54/PHANTOM/pull/" +
        str(barrier["test_pr"]) + ") was BLOCKED by failed required status in " +
        "[run " + str(barrier["policy_run"]) + "](https://github.com/barsam54/PHANTOM/actions/runs/" +
        str(barrier["policy_run"]) + ").",
        "- Current ruleset validated in this run: **NO**. Direct-push denial tested: **NO**.",
        "- Evidence: `" + barrier["evidence"] + "`.",
        "",
        "### Remaining blockers",
        "",
    ])
    for blocker in report["remaining"]:
        lines.append("- " + blocker)
    lines.extend([
        "",
        "### Audit links",
        "",
        "- [Source-first decision](../../blob/governance/p0-unified-controller-contract/docs/architecture/SOURCE-FIRST-DECISION.json)",
        "- [Controller contract](../../blob/governance/p0-unified-controller-contract/docs/architecture/GOVERNANCE-CONTRACT.json)",
        "- [PR #1 (DRAFT)](https://github.com/barsam54/PHANTOM/pull/1)",
        "",
        "This job is a visualization only. Full GOV-P0 remains **OPEN**.",
        "",
    ])
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json-out")
    p.add_argument("--markdown-out")
    opts = p.parse_args()
    try:
        report = inventory()
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "denial": {
            "code": "GOV_DISCOVERY_FAILED", "stage": "GOV-P0",
            "reason": str(exc), "evidence": [CONTRACT_PATH.as_posix()],
            "action": "Repair invalid/missing input; rerun governance inventory",
            "resume": "discover"
        }}, ensure_ascii=False))
        return 2
    as_json = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    as_markdown = markdown(report)
    for output, text in ((opts.json_out, as_json), (opts.markdown_out, as_markdown)):
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    print(as_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
