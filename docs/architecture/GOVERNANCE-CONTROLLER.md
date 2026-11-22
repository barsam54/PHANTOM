# PHANTOM | P0 Unified Development Governance Controller
Status: **OPEN — CONTRACT DOCUMENTED; END-TO-END EXECUTION NOT IMPLEMENTED**
Owner of scope: development governance across all project phases; not the research-product SML memory service.
Baseline: [BASELINE.md](BASELINE.md) section 12. Governing decision must not silently change existing accepted evidence or reopen SML-04.

## Architecture: one execution contract, five always-present views
Trigger: GitHub Actions, local CLI, or a future authorized agent runner.
Orchestration: **Microsoft Agent Framework C# workflow**, with explicit executors and conditional transitions. The framework's published APIs must be confirmed against the pinned package before implementation. GitHub Actions triggers/tests the controller; it does not become a second research workflow engine.
Inputs: immutable revision SHA, stage ID, baseline revision/criteria, existing evidence index, dependency graph, permissions, run ID.
Outputs: evidence manifest, decision (PASS / REPAIRABLE / BLOCKED / PENDING), denial with remedy, durable progress checkpoint, published status projected into GitHub Projects.
Separation: project SML state/memory/learning is **not** governance progress state. Never use scientific memory as the authoritative project task database.
Repositories: baseline, source, tests, sanitized evidence and acceptance contract remain versioned in Git. Large logs, datasets, checkpoints and secrets remain outside Git. Project dashboards contain derived displays, never independently asserted PASS.

## Five capabilities and mandatory templates
| Capability | Template / source of truth | Acceptable completion proof | Failure behavior |
| --- | --- | --- | --- |
| 1 Dashboard | `run_id, stage_id, commit_sha, accepted, pending, blocked, checkpoint_ref, action` projected from verified run manifest to GitHub Projects | graph/board matches accepted evidence, refresh confirmed | STALE_DASHBOARD -> refresh projection; never change PASS manually |
| 2 Evidence | `stage_id, criterion_id, code_sha, baseline_sha, test_id, run_id, environment, outcome, source_ref, evidence_digest` | readback, provenance/coverage and integrity verified; previous evidence reused only with matching scope | EVIDENCE_MISSING -> collect only missing proofs |
| 3 Phase lifecycle | `discover -> baseline_review -> dependencies -> plan -> authorized_execute -> build_and_tests -> evidence -> acceptance -> publish -> checkpoint` | actual phase finishes and survives an induced failure/restart without duplicated side effects | CHECKPOINT_INVALID -> restore validated checkpoint or BLOCKED with exact manual action |
| 4 Enforcement | `code, stage, reason, evidence, action, resume` with no blank fields; agent cannot self-approve | negative tests reject invalid change at actual merge/acceptance boundary | POLICY_DENIED -> deterministic explanation and remedy |
| 5 Baseline review | `baseline_sha, contested_clause, external_official_source, reproducible_finding, proposed_change, impact, approval` | routine fix proceeds; conflict remains blocked for the affected operation until reviewed amendment | BASELINE_CONFLICT -> isolated amendment PR; no silent edits or broad freeze |

### Progress manifest / decision template
```json
{
  "schema_version": "phantom.governance.v1",
  "run_id": "unique-id", "stage_id": "SML-02",
  "code_sha": "<full sha>", "baseline_sha": "<full sha>",
  "decision": "PENDING",
  "implemented": [], "verified": [], "remaining": [],
  "dependency_status": [], "evidence": [],
  "checkpoint_ref": null, "denial": null,
  "dashboard_synced": false
}
```
These are required *future* controller fields, **not a claim of an existing production manifest generator**. No dashboard sync implementation exists in this change.

### Denial / repair / resume template
```json
{
  "code": "EVIDENCE_MISSING",
  "stage": "SML-02",
  "reason": "Persistent restart/idempotency evidence absent",
  "evidence": ["docs/evidence/<existing-file>"],
  "action": "Run the declared persistent restart negative case; retain previous passing scope",
  "resume": "verification:resume-token-or-reference"
}
```
A denial must identify *what* violated *which* criterion, and supply an actionable way to continue; no blanket blocking unrelated tasks. Do not claim automatic repair without authorized worker, bounded retries and proven idempotency.

## External patterns: where to apply, and where not
**Microsoft (normative API reference, mandatory when implementing C# framework behavior)**
- Workflow/executor routing: discovery, plan, execute, verify and acceptance executors. https://learn.microsoft.com/en-us/agent-framework/workflows/workflows
- State: per-run isolation; **not** research memory. https://learn.microsoft.com/en-us/agent-framework/workflows/state
- Checkpoint/restart: use official C# APIs and persistent storage, then separately guard external side effects with idempotency keys. https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints
- Human-in-the-loop: security-critical, policy-weakening or non-delegated decisions only; do not require user intervention for routine fixes. https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop

**Anthropic (engineering practice; optional adaptation, not a required product)**
- A fresh run should read Git history, stage inventory and prior progress **before** planning work; commit small verified increments, leave durable progress notes and run end-to-end checks. https://www.anthropic.com/research/effective-harnesses-for-long-running-agents
- Do not use chats as durable state; do not introduce an Anthropic SDK or an autonomous loop with unrestricted repository rights.

**Tsinghua / ChatDev (research pattern only; NOT official Microsoft support)**
- Role separation: propose/implement/review with attribution, not multiple controllers.
- Experiential co-learning: store failure descriptions, verified remedies and scope as *advisory experiences*; a lesson is not a criterion or PASS. https://aclanthology.org/2024.acl-long.305/
- Do not use ChatDev to coordinate PHANTOM; implement any useful learned strategy within the existing framework and policies.

**GitHub (development system, outside Microsoft Agent Framework)**
- Actions job dependency, permissions and reusable workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- GitHub Actions does not guarantee rejection of a direct push without an enforceable branch rule. The current private main is unprotected; upgrade/publication/alternative enforcement needs separate security review.

## Sequencing: capability slices, ONE acceptance
A. Read and preserve earlier stage evidence. Keep existing repository layout guard, extend rather than delete it.
B. Supply machine-readable contract, structured denial and negative tests in existing policy workflow. **Initial guard only**: it can fail CI, cannot guarantee prevention of bypass.
C. Implement Governance Workflow in C# Agent Framework, durable checkpoint and bounded authorized worker. Confirm exact official .NET APIs first.
D. Publish evidence and PR automatically; independent verify step; update Projects via least-privilege GitHub integration.
E. Test real phase end-to-end: forced failure, restart, reuse of previous valid work, baseline conflict, false PASS rejection, dashboard coherence, and attempted invalid merge. Mark P0 PASS only when end-to-end tested on host.

## Acceptance exclusions
- No release; no opening previously accepted SML-04 operational scope.
- No Azure service dependency.
- No second orchestration engine or research-memory reuse for governance.
- No mandatory day-to-day manual commits, tests or evidence maintenance when P0 accepted.
- Do not declare P0 complete from schema checks or CI alone.

## Baseline review governance
Baseline is an authoritative *current contract*, not an infallible source. A contradiction is recorded with its clause, reproducible failing case, versioned official vendor reference, proposed replacement and affected gate. Standard conformant code changes do not require a baseline amendment. Security/scope/acceptance weakening requires separate approval, with CI guarding against silent reductions.

## Current implementation status
**DONE (historical)**: repository file/layout guard and its workflow; baseline, code, SML evidence and .NET CI exist.
**THIS CHANGE**: establishes contract, mapping, guard checks, tests; reports P0 as OPEN.
**NOT DONE**: full C# governance orchestrator, managed coding worker, persistent restart-safe progress, automated evidence publication, complete CI coverage, dashboard sync, and enforced protected branch. Do not label any of these PASS without independent evidence.
