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
        "remaining": ["durable governance phase execution", "evidence provenance and acceptance",
                      "bounded authorized worker", "forced failure/resume",
                      "automatic PR publication", "GitHub Projects synchronization",
                      "enforced merge barrier"]
    }


def markdown(report):
    lines = ["# PHANTOM Governance: discovery only", "",
             "Commit: " + report["commit_sha"], "",
             "**GOV-P0 OPEN. Historical files are NOT independently verified.**", "",
             "| Capability | Contract status | Independent proof | Required acceptance |",
             "| --- | --- | --- | --- |"]
    for item in report["capabilities"]:
        lines.append("| " + " | ".join([item["id"], item["contract_state"],
                                      "NOT VERIFIED", item["next_proof"]]) + " |")
    lines.extend(["", "Historical evidence files found: " +
                  str(report["historical_evidence_files_found"]) +
                  " (existence only; not evidence acceptance)", "",
                  "## Stage filename hints (NOT an acceptance conclusion)"])
    for gate, hints in report["stage_filename_hints_unverified"].items():
        lines.append("- " + gate + ": " + str(len(hints)) + " file name matches")
    lines.extend(["", "GitHub Projects synchronized: NO.", ""])
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
