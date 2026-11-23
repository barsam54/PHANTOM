#!/usr/bin/env python3
"""PHANTOM repository layout policy guard. Python standard library only."""
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {
    ".gitignore", ".gitattributes", ".editorconfig",
    "global.json", "Directory.Build.props", "Directory.Build.targets",
    "Directory.Packages.props", "NuGet.Config", "README.md",
    "LICENSE", "LICENSE.md", "PHANTOM.slnx",
}
ALLOWED_ROOT_DIRS = {
    "src", "tests", "benchmarks", "docs", "infra", "scripts", ".github",
}
BLOCKED_COMPONENTS = {"bin", "obj", "TestResults", "__pycache__", ".vs", ".idea"}
BLOCKED_SUFFIXES = {".sqlite", ".db", ".bak", ".backup", ".pfx", ".pem", ".key", ".trx", ".gguf", ".ggml", ".safetensors"}
BLOCKED_NAMES = {".env", "secrets.json", "appsettings.Development.json"}
BLOCKED_PREFIXES = ("artifacts/", "data/", "logs/", "backups/", "backup/")
MAX_EVIDENCE_BYTES = 256 * 1024


def tracked_files():
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip())
    return [p.decode("utf-8", errors="replace") for p in proc.stdout.split(b"\0") if p]


def check_path(path):
    problems = []
    parts = Path(path).parts
    if not parts:
        return problems
    if len(parts) == 1:
        if path not in ALLOWED_ROOT_FILES:
            problems.append(("ROOT_FILE_NOT_ALLOWED", "Move this file into an approved directory or explicitly amend the baseline."))
    elif parts[0] not in ALLOWED_ROOT_DIRS:
        problems.append(("ROOT_DIRECTORY_NOT_ALLOWED", f"Directory '{parts[0]}' is not in the approved layout."))
    if any(p in BLOCKED_COMPONENTS for p in parts):
        problems.append(("GENERATED_OUTPUT_TRACKED", "Generated output must not be committed."))
    if path.startswith(BLOCKED_PREFIXES):
        problems.append(("EXTERNAL_STORAGE_REQUIRED", "Runtime artifacts, datasets, and backups belong outside the repository."))
    name = parts[-1]
    if name in BLOCKED_NAMES or name.startswith(".env.") or Path(name).suffix.lower() in BLOCKED_SUFFIXES:
        problems.append(("SENSITIVE_OR_BINARY_ARTIFACT", "This file type is prohibited from version control."))
    if path.startswith("docs/evidence/"):
        target = ROOT / path
        if target.is_file() and target.stat().st_size > MAX_EVIDENCE_BYTES:
            problems.append(("EVIDENCE_TOO_LARGE", "Evidence files must be at most 256 KiB; store large artifacts externally."))
    return problems



GOVERNANCE_CONTRACT = "docs/architecture/GOVERNANCE-CONTRACT.json"
REQUIRED_GOVERNANCE_CAPABILITIES = {
    "dashboard", "evidence", "end_to_end", "enforcement", "baseline_review",
    "impact_rollback"
}
REQUIRED_DENIAL_FIELDS = {"code", "stage", "reason", "evidence", "action", "resume"}
REQUIRED_STAGE_STEPS = (
    "discover", "baseline_review", "dependencies", "plan", "authorized_execute",
    "build_and_tests", "evidence", "acceptance", "publish", "checkpoint"
)


def governance_denial(code, reason, action, evidence=None):
    """Actionable denial; this is a contract guard, not full P0 enforcement."""
    return {
        "path": GOVERNANCE_CONTRACT,
        "code": code,
        "stage": "GOV-P0",
        "reason": reason,
        "evidence": evidence or [GOVERNANCE_CONTRACT],
        "action": action,
        "resume": "rerun repository-policy after correcting the contract",
    }


def check_governance_contract(root=ROOT):
    """Fail closed on missing or malformed P0 contract. No model/host needed."""
    target = root / GOVERNANCE_CONTRACT
    if not target.is_file():
        return [governance_denial(
            "GOV_CONTRACT_MISSING", "P0 governance contract does not exist",
            "Restore the versioned governance contract and rerun the policy guard"
        )]
    try:
        doc = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [governance_denial(
            "GOV_CONTRACT_INVALID_JSON", f"Cannot parse P0 contract: {exc}",
            "Repair the contract JSON and rerun the policy guard"
        )]
    if not isinstance(doc, dict):
        return [governance_denial(
            "GOV_CONTRACT_INVALID", "Contract root must be a JSON object",
            "Restore the published governance contract schema"
        )]
    errors = []
    if doc.get("gate") != "GOV-P0" or doc.get("status") != "OPEN":
        errors.append(governance_denial(
            "GOV_PREMATURE_ACCEPTANCE",
            "The controller remains OPEN until real end-to-end acceptance evidence exists",
            "Keep GOV-P0 OPEN; close it only through separately verified integration acceptance"
        ))
    caps = doc.get("capabilities", [])
    ids = [item.get("id") for item in caps if isinstance(item, dict)] if isinstance(caps, list) else []
    if set(ids) != REQUIRED_GOVERNANCE_CAPABILITIES or len(ids) != len(REQUIRED_GOVERNANCE_CAPABILITIES):
        errors.append(governance_denial(
            "GOV_CAPABILITY_MISMATCH", "Exactly six approved complementary capabilities are required",
            "Restore all six capability IDs without duplicates or an additional controller"
        ))
    if not isinstance(caps, list) or any(
        not isinstance(item, dict) or item.get("state") != "OPEN" or not item.get("proof")
        for item in caps
    ):
        errors.append(governance_denial(
            "GOV_CAPABILITY_EVIDENCE_REQUIRED", "Capability status/proof incomplete or falsely closed",
            "Retain OPEN and give the acceptance proof needed for each capability"
        ))
    impact = doc.get("impact_rollback")
    required_impact_fields = {
        "change_id", "base_sha", "candidate_sha", "affected_components",
        "criteria_revision", "metric_definitions", "baseline_results",
        "candidate_results", "comparison_result", "regression_findings",
        "risk_class", "rollback_target_sha", "rollback_plan",
        "rollback_test_evidence", "post_change_monitoring", "decision_evidence"
    }
    required_comparisons = {"IMPROVED", "EQUIVALENT", "REGRESSION", "INCONCLUSIVE"}
    if not isinstance(impact, dict) or impact.get("state") != "OPEN":
        errors.append(governance_denial(
            "GOV_IMPACT_CONTRACT_MISSING",
            "Impact and rollback acceptance remains unimplemented or undocumented",
            "Restore impact_rollback in OPEN state; do not claim live rollback capability"
        ))
    else:
        fields = impact.get("required_fields")
        comparisons = impact.get("comparisons")
        rules = impact.get("acceptance_rules")
        if (not isinstance(fields, list) or set(fields) != required_impact_fields
                or len(fields) != len(required_impact_fields)
                or not isinstance(comparisons, list)
                or set(comparisons) != required_comparisons
                or len(comparisons) != len(required_comparisons)
                or not isinstance(rules, list) or len(rules) < 6
                or any(not isinstance(rule, str) or not rule.strip() for rule in rules)):
            errors.append(governance_denial(
                "GOV_IMPACT_CRITERIA_INCOMPLETE",
                "Before/after metric definitions, decisions or rollback proof fields missing",
                "Restore declared before/after, risk, recovery and post-rollback criteria"
            ))
    source_first = doc.get("source_first")
    expected_source_fields = {
        "decision_id", "scope", "problem", "baseline_ref", "candidate_solutions",
        "chosen_option", "why_existing_solution_is_insufficient", "official_sources",
        "evaluation_method", "expected_impact", "rollback_risk", "status"
    }
    if (not isinstance(source_first, dict)
            or source_first.get("state") != "OPEN"
            or source_first.get("decision_record") != SOURCE_DECISION_FILE
            or set(source_first.get("required_fields", [])) != expected_source_fields
            or source_first.get("no_invention_without_evidence") is not True):
        errors.append(governance_denial(
            "GOV_SOURCE_FIRST_CONTRACT_INVALID",
            "Mandatory source-first/reuse-first contract missing or weakened",
            "Restore the reviewed source-first decision contract and negative checks",
            [GOVERNANCE_CONTRACT, SOURCE_DECISION_FILE]))
    if doc.get("phase_steps") != list(REQUIRED_STAGE_STEPS):
        errors.append(governance_denial(
            "GOV_STAGE_CONTRACT_MISMATCH", "End-to-end stage contract is missing or reordered",
            "Restore the declared phase steps or submit a reviewed baseline amendment"
        ))
    fields = doc.get("denial_fields", [])
    if not isinstance(fields, list) or set(fields) != REQUIRED_DENIAL_FIELDS or len(fields) != len(REQUIRED_DENIAL_FIELDS):
        errors.append(governance_denial(
            "GOV_DENIAL_FIELDS_MISSING", "Denial must report code/stage/reason/evidence/action/resume",
            "Restore the six actionable-denial fields"
        ))
    if doc.get("release_allowed") is not False:
        errors.append(governance_denial(
            "GOV_RELEASE_BLOCKED", "Release is prohibited before whole-project approval",
            "Set release_allowed to false; obtain separately reviewed release approval"
        ))
    for field in ("baseline", "controller_spec"):
        path = doc.get(field)
        if (not isinstance(path, str) or not path.startswith("docs/architecture/")
                or ".." in Path(path).parts or not (root / path).is_file()):
            errors.append(governance_denial(
                "GOV_REFERENCE_MISSING", f"{field} must reference an existing architecture document",
                "Restore its checked-in document path and content"
            ))
    return errors


SOURCE_DECISION_FILE = "docs/architecture/SOURCE-FIRST-DECISION.json"
SOURCE_REQUIRED_FIELDS = {
    "decision_id", "scope", "problem", "baseline_ref", "candidate_solutions",
    "chosen_option", "why_existing_solution_is_insufficient", "official_sources",
    "evaluation_method", "expected_impact", "rollback_risk", "status"
}
SOURCE_REFERENCE_FIELDS = {
    "provider", "url", "applies_to", "reviewed_version", "verification"
}


def check_source_first_decision(root=ROOT):
    """Bootstrap integrity gate, NOT validation that vendor docs are accurate."""
    target = root / SOURCE_DECISION_FILE
    if not target.is_file():
        return [governance_denial(
            "GOV_SOURCE_DECISION_MISSING",
            "Source-first decision record is missing",
            "Register the official-source/reuse review before approving architecture",
            [SOURCE_DECISION_FILE])]
    try:
        record = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [governance_denial(
            "GOV_SOURCE_DECISION_INVALID_JSON", f"Source decision is unreadable: {exc}",
            "Repair the JSON and rerun governance admission",
            [SOURCE_DECISION_FILE])]
    if not isinstance(record, dict):
        return [governance_denial(
            "GOV_SOURCE_DECISION_INVALID", "Source decision must be a JSON object",
            "Restore the approved structured decision format",
            [SOURCE_DECISION_FILE])]
    errors = []
    for field in SOURCE_REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or value == "" or value == []:
            errors.append(governance_denial(
                "GOV_SOURCE_FIELD_MISSING", f"Decision field {field} is required",
                "Record review evidence and an explicit comparison before proceeding",
                [SOURCE_DECISION_FILE]))
    choices = record.get("candidate_solutions")
    if not isinstance(choices, list) or len(choices) < 2 or any(
        not isinstance(item, dict) or not all(item.get(k) for k in
        ("id", "kind", "reference", "outcome", "reason"))
        for item in choices
    ):
        errors.append(governance_denial(
            "GOV_REUSE_COMPARISON_MISSING",
            "At least two explicit reuse/extend/build options with reasons are required",
            "Compare existing supported solutions against any proposed new implementation",
            [SOURCE_DECISION_FILE]))
    elif record.get("chosen_option") not in {x["id"] for x in choices}:
        errors.append(governance_denial(
            "GOV_SOURCE_CHOICE_UNREFERENCED", "Selected option does not exist in the comparison",
            "Select an explicitly assessed candidate option", [SOURCE_DECISION_FILE]))
    sources = record.get("official_sources")
    permitted_hosts = {"learn.microsoft.com", "docs.github.com", "docs.ollama.com"}
    if not isinstance(sources, list) or not sources or any(
        not isinstance(item, dict) or not SOURCE_REFERENCE_FIELDS.issubset(item)
        or any(not isinstance(item.get(key), str) or not item[key].strip()
               for key in SOURCE_REFERENCE_FIELDS)
        or urlparse(item["url"]).scheme != "https"
        or urlparse(item["url"]).hostname not in permitted_hosts
        for item in sources
    ):
        errors.append(governance_denial(
            "GOV_OFFICIAL_SOURCE_INVALID",
            "Source reference must include a verified-scope official HTTPS URL, applicable version and evidence",
            "Cite vendor primary documentation and record version-specific verification",
            [SOURCE_DECISION_FILE]))
    if record.get("status") not in {"PROPOSED", "EVIDENCE_REVIEWED", "APPROVED"}:
        errors.append(governance_denial(
            "GOV_SOURCE_STATUS_INVALID",
            "Source review status is unknown",
            "Use PROPOSED, EVIDENCE_REVIEWED, or separately approved APPROVED",
            [SOURCE_DECISION_FILE]))
    return errors


def main():
    try:
        paths = tracked_files()
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "reason": "GIT_INDEX_UNAVAILABLE", "details": str(exc)}, ensure_ascii=False))
        return 2
    violations = [
        {"path": path, "code": code, "reason": reason}
        for path in paths for code, reason in check_path(path)
    ]
    violations.extend(check_governance_contract())
    violations.extend(check_source_first_decision())
    report = {"status": "FAIL" if violations else "PASS", "checked_files": len(paths), "violations": violations}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if violations:
        print("POLICY GUARD FAILED: see path, code and reason above.", file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
