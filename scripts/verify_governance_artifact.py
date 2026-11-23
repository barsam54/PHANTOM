#!/usr/bin/env python3
"""Independent, fail-closed GitHub artifact readback with scoped cache reuse."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile

SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
BASELINE = "docs/architecture/BASELINE.md"
CONTRACT = "docs/architecture/GOVERNANCE-CONTRACT.json"
STEPS = ("discover", "baseline_review", "dependencies", "plan", "authorized_execute",
         "build_and_tests", "evidence", "acceptance", "publish", "checkpoint")
CAPS = {"dashboard", "evidence", "end_to_end", "enforcement", "baseline_review", "impact_rollback"}
CRITERION = "governance.policy_ci"
MAX_ZIP = 8 * 1024 * 1024
MAX_EXPANDED = 12 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def denial(code, reason):
    return {"status": "BLOCKED", "code": code, "reason": reason,
            "criterion_verified": False, "governance_acceptance": "OPEN"}


def fetch(url, token=None):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "PHANTOM-evidence-readback",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            data = response.read(MAX_ZIP + 1)
            if len(data) > MAX_ZIP:
                raise ValueError("PROVIDER_RESPONSE_TOO_LARGE")
            return data
    except HTTPError as error:
        from urllib.parse import urlparse
        safe = urlparse(url)
        raise ValueError("PROVIDER_HTTP_%d_AT_%s%s" % (
            error.code, safe.hostname, safe.path)) from error


def inspect_archive(archive, metadata, expected_sha, contract_bytes, baseline_bytes):
    if len(archive) > MAX_ZIP or metadata.get("digest") != "sha256:" + sha(archive):
        return denial("ARCHIVE_DIGEST_MISMATCH", "Archive SHA-256 does not match GitHub")
    try:
        with ZipFile(io.BytesIO(archive)) as z:
            entries = z.namelist()
            if (len(entries) != len(set(entries)) or
                any(n.startswith("/") or "\\" in n or ".." in PurePosixPath(n).parts for n in entries) or
                sum(i.file_size for i in z.infolist()) > MAX_EXPANDED):
                return denial("ARCHIVE_STRUCTURE_INVALID", "Unsafe or oversized ZIP")
            names = {PurePosixPath(n).name: n for n in entries if not n.endswith("/")}
            if len(names) != len([n for n in entries if not n.endswith("/")]):
                return denial("ARCHIVE_STRUCTURE_INVALID", "Ambiguous evidence paths")
            required = ("governance-inventory.json", "governance-phase0-ten-steps.json")
            if any(name not in names for name in required):
                return denial("EVIDENCE_CONTENT_MISSING", "Expected reports missing")
            inv, probe = (json.loads(z.read(names[name])) for name in required)
    except (BadZipFile, ValueError, KeyError, UnicodeError, OSError, TypeError) as exc:
        return denial("ARCHIVE_UNREADABLE", type(exc).__name__)
    try:
        contract = json.loads(contract_bytes)
        if (inv.get("commit_sha") != expected_sha or probe.get("sha") != expected_sha or
            inv.get("contract_digest_sha256") != sha(contract_bytes) or
            probe.get("contract_sha256") != sha(contract_bytes) or
            inv.get("baseline_digest_sha256") != sha(baseline_bytes)):
            return denial("PINNED_SOURCE_MISMATCH", "Evidence differs from pinned sources")
        if (contract.get("gate") != "GOV-P0" or contract.get("status") != "OPEN" or
            contract.get("baseline") != BASELINE or
            "## 12. P0" not in baseline_bytes.decode("utf-8") or
            len(contract.get("capabilities", [])) != 6 or
            {c.get("id") for c in contract["capabilities"]} != CAPS):
            return denial("CONTRACT_SCOPE_INVALID", "Contract/baseline criteria invalid")
        caps = inv.get("capabilities", [])
        if (inv.get("gate") != "GOV-P0" or inv.get("decision") != "OPEN" or
            len(caps) != 6 or {c.get("id") for c in caps} != CAPS or
            any(c.get("verified") is not False or c.get("contract_state") != "OPEN" for c in caps)):
            return denial("FALSE_ACCEPTANCE_OR_COVERAGE", "Capability proof/decision inconsistent")
        steps = probe.get("steps", [])
        if (probe.get("phase") != "GOV-P0" or probe.get("overall_acceptance") != "OPEN" or
            probe.get("all_steps_executed") is not False or
            [s.get("step") for s in steps] != list(STEPS) or
            any(not all(s.get(k) for k in ("code", "reason", "action", "resume")) for s in steps)):
            return denial("PROBE_CRITERIA_INVALID", "Ten-step evidence mismatched")
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        return denial("REPORT_FORMAT_INVALID", type(exc).__name__)
    return {"status": "CHECK_OK", "criterion_verified": True,
            "criterion": CRITERION, "content_readback_verified": True,
            "code_sha": expected_sha, "archive_sha256": sha(archive),
            "governance_acceptance": "OPEN"}



def checkout_sha_from_archive(archive):
    """Read untrusted candidate checkout SHA; GitHub must attest its parents next."""
    if len(archive) > MAX_ZIP:
        raise ValueError("ARCHIVE_OVERSIZED")
    with ZipFile(io.BytesIO(archive)) as zipped:
        names = zipped.namelist()
        matching = [n for n in names if PurePosixPath(n).name == "governance-inventory.json"]
        if len(matching) != 1:
            raise ValueError("CHECKOUT_REPORT_MISSING")
        if zipped.getinfo(matching[0]).file_size > MAX_EXPANDED:
            raise ValueError("CHECKOUT_REPORT_OVERSIZED")
        sha_value = json.loads(zipped.read(matching[0])).get("commit_sha")
    if not isinstance(sha_value, str) or not SHA.fullmatch(sha_value):
        raise ValueError("CHECKOUT_SHA_INVALID")
    return sha_value


def verify_live(repo, run_id, expected_sha, cache_dir, token=None, read=fetch):
    if not REPO.fullmatch(repo or "") or not SHA.fullmatch(expected_sha or "") or run_id <= 0:
        return denial("INVALID_REQUEST", "Expected repository, positive run id and full SHA")
    base = "https://api.github.com/repos/" + repo + "/actions/"
    run = json.loads(read(base + "runs/" + str(run_id), token))
    jobs = json.loads(read(base + "runs/" + str(run_id) + "/jobs?per_page=100", token))
    artifacts = json.loads(read(base + "runs/" + str(run_id) + "/artifacts?per_page=100", token))
    if (run.get("id") != run_id or run.get("head_sha") != expected_sha or
        run.get("event") != "pull_request" or run.get("name") != "Repository Policy Guard" or
        run.get("status") != "completed" or run.get("conclusion") != "success"):
        return denial("RUN_PROVENANCE_INVALID", "Pinned workflow must succeed")
    entries = jobs.get("jobs", [])
    if (jobs.get("total_count", 0) > 100 or artifacts.get("total_count", 0) > 100 or
        not entries or any(j.get("status") != "completed" or j.get("conclusion") != "success" for j in entries)):
        return denial("JOB_PROVENANCE_INVALID", "Unverified, incomplete or failed jobs")
    matches = [a for a in artifacts.get("artifacts", []) if a.get("name") == "governance-inventory"]
    if len(matches) != 1:
        return denial("ARTIFACT_AMBIGUOUS", "Required artifact absent or duplicated")
    art = matches[0]
    origin = art.get("workflow_run") or {}
    if (art.get("expired") is not False or origin.get("id") != run_id or
        origin.get("head_sha") != expected_sha or not DIGEST.fullmatch(art.get("digest") or "") or
        not isinstance(art.get("id"), int) or art["id"] <= 0):
        return denial("ARTIFACT_PROVENANCE_INVALID", "Artifact digest/run binding invalid")
    cache_dir = Path(cache_dir)
    target = cache_dir / ("run-%d-artifact-%d-%s.zip" % (run_id, art["id"], expected_sha))
    reused = False
    if target.exists() and target.stat().st_size <= MAX_ZIP:
        archive = target.read_bytes()
        reused = sha(archive) == art["digest"][7:]
    if not reused:
        archive = read(base + "artifacts/" + str(art["id"]) + "/zip", token)
    checkout_sha = checkout_sha_from_archive(archive)
    # GitHub PR workflows check out a synthetic merge commit (base + head).
    # Check the actual commit parents through GitHub rather than trusting the ZIP.
    checkout_commit = json.loads(read("https://api.github.com/repos/" + repo +
                                      "/commits/" + checkout_sha, token))
    parents = checkout_commit.get("parents", [])
    if (checkout_commit.get("sha") != checkout_sha or len(parents) != 2 or
        parents[1].get("sha") != expected_sha):
        return denial("CHECKOUT_PARENT_MISMATCH",
                      "Evidence checkout is not a GitHub merge of this PR head")
    prefix = "https://raw.githubusercontent.com/" + repo + "/" + checkout_sha + "/"
    contract = read(prefix + CONTRACT, None)
    baseline = read(prefix + BASELINE, None)
    result = inspect_archive(archive, art, checkout_sha, contract, baseline)
    if result["status"] != "CHECK_OK":
        return result
    if not reused:
        cache_dir.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(".tmp")
        temp.write_bytes(archive)
        temp.replace(target)
    result.update({"run_id": run_id, "artifact_id": art["id"],
                   "archive_reused": reused, "checkout_sha": checkout_sha,
                   "pr_head_sha": expected_sha, "ci_tests_reexecuted": False,
                   "verified_against_live_provider": True})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    try:
        result = verify_live(args.repo, args.run_id, args.expected_sha, args.cache_dir,
                             token=os.environ.get("GITHUB_TOKEN"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError,
            KeyError, TypeError) as exc:
        result = denial("READBACK_FAILED", type(exc).__name__ + ": " + str(exc))
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(output, encoding="utf-8")
    print(output)
    return 0 if result["status"] == "CHECK_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
