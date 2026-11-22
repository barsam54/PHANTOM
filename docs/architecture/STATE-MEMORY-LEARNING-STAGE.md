# PHANTOM | State, Memory, Learning Stage

Status: OPEN — initial isolation tests HOST PASS; direct state/checkpoint/memory/learning gates PENDING
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
