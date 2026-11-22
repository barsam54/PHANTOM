# PHANTOM | State, Memory, Learning Stage

Status: OPEN — isolation and in-memory checkpoint tests HOST PASS; remaining gates PENDING
Started: 2026-11-22
Baseline: `docs/architecture/BASELINE.md` §§3, 6, 7, 9A

## Scope and separation

1. **Execution state:** transient per-run data and executor context, owned by Microsoft Agent Framework workflow runtime. Never share mutable per-experiment state across unrelated runs.
2. **Checkpoint:** framework-supported snapshot for resuming an interrupted workflow. A checkpoint is not a scientific memory or proof of learning.
3. **Research memory:** explicitly versioned, provenance-linked results retained beyond a run, stored outside the source tree. Reads must be scoped to the permitted experiment/dataset split.
4. **Learning:** measurable improvement against a frozen evaluation protocol and independent held-out evidence. Persisting state or accumulating observations does not count as learning.

## Architectural decisions

- Microsoft Agent Framework remains the only workflow orchestrator. No parallel custom state machine, scheduler, or workflow runner.
- Use framework workflow state/checkpoint APIs only after verifying the **pinned C# package version** supports the exact chosen API. Do not copy Python-only APIs into C#.
- Distinct experiment runs must not reuse agent sessions/executor state by accident; if reuse is intentional, document reset and ownership semantics.
- Checkpoint and research-memory storage are separate concerns. Both require explicit storage location, ownership, integrity checks, and access boundaries.
- No automatic promotion of evaluation/test results into training memory. Future-data leakage prevention is a mandatory acceptance gate.
- State and memory contracts must include schema/version, experiment identity, provenance, and failure semantics before persistence code is added.
- Learning requires a fixed baseline, a declared metric, held-out validation and regression checks; no self-declared PASS.

## Stage-specific acceptance criteria

| ID | Gate | Required evidence |
| --- | --- | --- |
| SML-01 | State isolation | Concurrent independent experiment runs cannot read each other's private state. |
| SML-02 | Resume correctness | Framework checkpoint restore resumes without duplicating completed side effects; interrupted/invalid checkpoint negative cases tested. |
| SML-03 | Memory provenance | Persisted record has schema version, source/evidence reference and deterministic identity; readback and corruption rejection tested. |
| SML-04 | Access and leakage | Unrelated experiments and future/held-out observations are rejected by policy, including negative tests. |
| SML-05 | Learning validity | A frozen benchmark and held-out comparison show a reproducible improvement, with explicit FAIL on no improvement. |
| SML-06 | Integration/regression | Agent Framework integration tests, build and existing regression suite PASS on host; sanitized evidence committed. |

No criterion is marked PASS based on this design document.

## Implementation progress (2026-11-22)

- Reviewed current `FirstWorkflow.RunAsync`: it creates fresh executor bindings and builds a fresh Microsoft Agent Framework workflow for each call; no workflow instance is cached or shared.
- Added `tests/Phantom.Infrastructure.Tests/WorkflowStateIsolationTests.cs` in commit `65d8c0f`. It checks 12 simultaneous distinct workflow inputs and a sequential fresh-run case.
- **HOST PASS (2026-11-22)**: 26/26 full infrastructure tests passed (0 failed, 0 skipped), including both new isolation tests; see `docs/evidence/2026-11-22-state-isolation-verification.md`. SML-01 is still OPEN until direct framework state isolation is verified.
- This tests observable input/output isolation only, not the framework's private/shared `IWorkflowContext` state. Add direct state-scope tests when state is actually used.
- SML-02 through SML-06 remain OPEN; no checkpoint, research memory or learning implementation is claimed.

## Verified .NET checkpoint API review (2026-11-22)

Official Microsoft documentation explicitly shows these C# APIs:

- `CheckpointManager.CreateInMemory()`
- `InProcessExecution.RunStreamingAsync(workflow, input, checkpointManager)`
- `StreamingRun.WatchStreamAsync()` and `StreamingRun.Checkpoints`
- `SuperStepCompletedEvent.CompletionInfo?.Checkpoint`
- `run.RestoreCheckpointAsync(savedCheckpoint)`

Reference: https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints

The current PHANTOM `FirstWorkflow.RunAsync` uses `InProcessExecution.RunAsync` and returns the reverse executor output from `run.NewEvents`. Do not replace this stable production path solely to introduce checkpoint tests. Introduce a dedicated test-only streaming workflow first, using the same Agent Framework orchestration primitives.

**Important boundary:** framework checkpoints capture execution state after supersteps, not a guarantee of exactly-once external side effects. SML-02 must test interrupted/resumed execution, checkpoint identity/topology compatibility, and explicit side-effect idempotency. An in-memory manager is not durable across process restarts; durable recovery remains OPEN until a supported persistence provider and restoration test are established.

**Version boundary:** documentation shows the C# surface, but compilation against the repository-pinned `Microsoft.Agents.AI.Workflows` 1.28.0 and observed host execution are still required before marking any API integration PASS.

## Architecture decision: checkpoints are not research memory (2026-11-22)

**Decision:** keep workflow checkpoints, research memory, and learning evidence as distinct stores/contracts. This is required by Baseline §6.

- **Checkpoint:** transient executor/runtime state, pending messages and workflow continuation. Use Microsoft Agent Framework checkpoint APIs. In-memory checkpoint managers are not durable across process restart.
- **Research memory:** durable, explicitly versioned research observations and experiment outcomes, keyed by experiment ID and content fingerprint, with code/data version, provenance, evaluation status, observation cutoff time, dataset partition and evidence reference. Persist outside Git in a configurable store.
- **Learning:** an independently measured improvement relative to a frozen baseline and held-out test data; not a count of stored observations.

Memory admission must fail closed for missing provenance, unverified evaluation, incompatible schema, future observation relative to the research cutoff, or held-out/test partition leakage. Retrieval must enforce experiment/partition access and temporal eligibility. No automatic training-memory promotion.

Implementation boundary: checkpoint data must never be used as the authoritative research-memory database. Memory persistence must not introduce a second workflow orchestrator. Before selecting a C# persistence implementation, inspect existing contracts/storage and define schema migration, atomic write, integrity and negative-test behavior.

References: https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints and https://learn.microsoft.com/en-us/agent-framework/workflows/state

## Next checkpoint acceptance slice

1. Add a minimal isolated streaming workflow integration test with in-memory checkpoints; assert checkpoint capture after supersteps.
2. Restore a checkpoint and verify expected output and executor call counts, including a negative case for incompatible or missing checkpoint.
3. Keep external side effects behind an idempotent experiment-operation key; verify no duplicated committed effects on resume.
4. Verify the pinned package compiles and run the full regression suite on host; commit sanitized evidence.
5. Address persistent checkpoints separately. Do not claim crash/restart recovery from in-memory tests.

## Checkpoint test implementation (2026-11-22)

- Added `tests/Phantom.Infrastructure.Tests/WorkflowCheckpointTests.cs` (commit `ebefdec`).
- This is an isolated two-executor streaming test using documented C# `CheckpointManager.CreateInMemory`, `RunStreamingAsync`, `WatchStreamAsync`, `Checkpoints`, and `RestoreCheckpointAsync` APIs.
- It asserts original output, checkpoint availability, and output after restoring an intermediate checkpoint.
- **HOST PASS (2026-11-22)** against pinned package 1.28.0: 27/27 full infrastructure tests succeeded, 0 failed, 0 skipped. See `docs/evidence/2026-11-22-checkpoint-verification.md`. SML-02 remains OPEN for persistent restart, negative recovery, and idempotent side-effect coverage.
- This test does not establish persistent restart recovery or external side-effect idempotency. Those require separate tests.

## Research-memory admission contract (2026-11-22)

- Added `src/Phantom.AgentFramework/ResearchMemoryAdmission.cs` (`9875d91`) and seven positive/negative MSTest cases (`5995321`).
- Admission checks explicit provenance, SHA-256 fingerprint shape, absolute file evidence URI, UTC timestamps, observation cutoff, training partition and positive evaluation.
- **HOST PASS (2026-11-22):** full suite 34/34 succeeded, 0 failed/skipped. Evidence: `docs/evidence/2026-11-22-memory-admission-verification.md`. This is a pure validation slice, not a durable memory store. It does not yet authenticate evidence, verify file contents, enforce access control on retrieval, or prove learning. SML-03/04 remain OPEN.
- `SchemaVersion = 1` identifies the initial contract; schema migration and persistence are still to be designed before any storage implementation.

## Evidence integrity slice (2026-11-22)

- Added `ResearchMemoryEvidenceVerifier.VerifyAsync` to verify actual local evidence file bytes against the declared SHA-256 fingerprint after admission validation. A mismatch is rejected; no content is written to memory.
- Added three MSTest cases: matching hash, tampered evidence and missing evidence.
- Commits: `faefd0a` (implementation), `cd2dcfa` (tests).
- **HOST PASS (2026-11-22)**: full suite 37/37 succeeded, 0 failed/skipped; see `docs/evidence/2026-11-22-memory-integrity-verification.md`.
- **Boundary:** a matching hash verifies consistency with a supplied digest, **not authenticity** of its source. This does not yet bind the digest to signed/trusted experiment evidence, establish read authorization, or implement persistent memory. SML-03 and SML-04 remain OPEN.

## Local durable memory manifest slice (2026-11-22)

- Added `ResearchMemoryStore` (`a512664`), a minimal immutable JSON manifest store in a caller-supplied absolute external directory. Each record includes schema version and the existing provenance/admission contract.
- Writes use `FileMode.CreateNew` to reject duplicate experiment IDs; reads revalidate the schema, experiment identity, admission rules and evidence-file SHA-256.
- Added three tests (`9c76c5b`): persistence/readback across new store instances, duplicate rejection and evidence tampering; unsafe/unknown experiment IDs; unsupported schema.
- **HOST PASS (2026-11-22)**: 40/40 succeeded after correcting missing-directory read behavior (initial run 39/40; root cause documented). Evidence: `docs/evidence/2026-11-22-memory-store-failure.md` and `docs/evidence/2026-11-22-memory-store-verification.md`. No SML-03/SML-04 closure is claimed.
- **Security and durability limits:** caller must secure the storage directory; this slice has no authorization boundary, signature verification, multi-process transaction protocol, symlink hardening, fsync guarantee, schema migration, or crash/power-loss recovery test. It is a local manifest store, not a production multi-tenant memory service or learning engine.
- Do not attach this store automatically to Agent Framework workflows until access policy and provenance authenticity are verified.

## Research cutoff-scoped retrieval (2026-11-22)

- Added `ResearchMemoryStore.ReadForResearchAsync` (`d6ab90d`), requiring an explicit UTC research cutoff. It reuses validated readback, then rejects observations or stored research cutoffs beyond the caller's permitted cutoff and rejects non-training partitions.
- Added positive and negative test cases (`bd36157`) for permitted read, disallowed earlier cutoff and non-UTC request.
- **HOST PASS (2026-11-22)**: full suite 41/41 succeeded, 0 failed/skipped, duration 1s 928ms; evidence: `docs/evidence/2026-11-22-memory-scoped-read-verification.md`. The policy test scope passed, but SML-04 remains OPEN for authenticated authorization and experiment isolation.
- **Limit:** the caller supplies the cutoff. This is an eligibility guard, **not authentication, tenant authorization, or a trust boundary**. An authenticated policy context and storage access restrictions remain required.

## Explicit experiment-scope retrieval (2026-11-22)

- Added `ReadForAuthorizedExperimentAsync` (`3752242`), which rejects a requested experiment ID not matching the caller-supplied authorized experiment ID **before opening any file**. It then applies existing temporal and evidence checks.
- Added a positive/negative MSTest case (`24be149`), including cross-experiment and missing authorization scope.
- **HOST PASS (2026-11-22):** full suite 42/42 succeeded, 0 failed/skipped; duration 1s 882ms. Evidence: `docs/evidence/2026-11-22-memory-experiment-scope-verification.md`. SML-04 remains OPEN because authenticated authorization and lower-level access restrictions are not implemented.
- **Security boundary:** this is a scoped-read API, not authentication. The caller must establish the authorized experiment ID from a trusted identity/policy service and restrict access to lower-level `ReadAsync` and filesystem paths. Without that, a caller could supply its own authorization ID. No end-to-end tenant security claim is made.

## Implementation order

1. Inspect pinned C# Agent Framework APIs and current workflow construction to select supported state isolation and checkpoint primitives.
2. Add narrowly scoped state-isolation and checkpoint-resume tests and implementation.
3. Define and implement versioned research-memory contract and provenance guards.
4. Define held-out learning evaluation protocol; only then implement learning.
5. Record host test evidence and limitations; close stage only after all criteria PASS.

## Official documentation reviewed

- Microsoft Agent Framework overview: https://learn.microsoft.com/en-us/agent-framework/overview
- Workflow state: https://learn.microsoft.com/en-us/agent-framework/workflows/state
- Workflow checkpoints: https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints

These describe framework concepts; concrete C# APIs must be verified against the project's pinned package before coding.
