# PHANTOM
## Baseline Laboratory Architecture

Status: OPEN
Implementation: IN PROGRESS (all five initial acceptance gates PASS for deterministic local workflow scope; full scientific and operational baseline OPEN)

### 1. Goal

PHANTOM is a research laboratory whose research,
experimentation, evaluation, and evidence workflows
are coordinated through Microsoft Agent Framework.

Principles:
- One central workflow orchestration framework
- Separation of orchestration from domain logic
- Testability and reproducibility
- Evidence-based acceptance
- No PASS without verified results

### 2. Technology Baseline

| Responsibility | Technology |
|---|---|
| Core language | C# |
| Runtime | .NET |
| Orchestration | Microsoft Agent Framework |
| Agents and workflows | Microsoft Agent Framework |
| Software testing | MSTest |
| Test execution | Microsoft.Testing.Platform |
| Agent evaluation | Agent Framework evaluation capabilities |
| Observability | Agent Framework observability |
| Development | VS Code |
| Isolation | Docker |
| Version control | Git / GitHub |

Exact package versions require verification against
official documentation before implementation.

### 3. Logical Architecture

PHANTOM
- Microsoft Agent Framework
  - Agents
  - Workflows
  - Tools and integrations
  - State and context
  - Observability
- Research Components
  - Market Data
  - Research Logic
  - Experiment Execution
  - Result Analysis
- Testing and Evaluation
  - MSTest
  - Microsoft.Testing.Platform
  - Agent Evaluation
  - Workflow Evaluation
- Infrastructure
  - Docker
  - Git
  - Evidence Storage

These are logical responsibilities, not claims about
official Microsoft package or class names.

### 4. Workflow Responsibilities

- Receive research requests
- Invoke relevant components
- Transfer outputs between stages
- Control execution order
- Invoke evaluation
- Return results and evidence

No parallel custom workflow orchestration engine.

### 5. Testing

Software tests:
- Unit tests
- Integration tests
- Input validation
- Error handling
- Deterministic reproducibility

Agent and workflow evaluation:
- Agent output evaluation
- Workflow evaluation
- Expected behavior verification
- Component-level evaluation
- Evaluation result recording

Domain-specific tests:
- Market data correctness
- Experiment reproducibility
- Prevention of future-data leakage
- Statistical evaluation

Domain-specific scientific criteria are not presented
as built-in Microsoft Agent Framework standards.

### 6. State, Memory, and Learning

State: current execution state.
Memory: retained information for later use.
Learning: measurable improvement based on results.

State and memory alone do not constitute learning.

Learning contracts and acceptance tests remain OPEN.

### 7. Evidence

Each experiment must record:
- Experiment ID
- Code version
- Input specification
- Execution configuration
- Test result
- PASS / FAIL status
- Evidence location

Workflow completion alone does not imply success.

### 8. Architectural Boundaries

- Agent Framework does not replace domain computation.
- MSTest does not replace scientific evaluation.
- Docker does not replace workflow orchestration.
- Execution state does not replace learning.
- Successful execution does not prove research validity.

### 9. Acceptance Gates

Initial acceptance gate status (verified on host 2026-11-22; CI results user-reported):
1. PASS — real two-executor Agent Framework workflow smoke.
2. PASS — MSTest via Microsoft.Testing.Platform; 18/18 tests.
3. PASS — LocalEvaluator evaluates actual workflow output, including positive and negative cases.
4. PASS — structured experiment/evaluation JSON persisted and read back.
5. PASS — independent deterministic workflow reruns reproduce evidence fingerprints; changed expected output fails.

Evidence: `docs/evidence/2026-11-22-gate4-gate5-verification.md` and `docs/evidence/2026-11-22-ci-verification.md`.
These five gates are CLOSED only for the implemented deterministic local infrastructure scope. Overall baseline remains OPEN for model-backed evaluation, observability, state/memory/learning, domain-scientific validation, secure research execution, backup recovery, and cross-environment reproducibility.

### 9A. Mandatory Stage-Specific Verification Policy

Every implementation stage must define acceptance criteria before marking PASS:
- Stage-specific tests cover its functional contract and negative/error cases.
- Existing tests remain in regression coverage; changes must not silently remove coverage.
- Integration tests verify the stage's connection to Microsoft Agent Framework when applicable.
- Build and test execution are verified together; a successful build alone is not acceptance.
- Small sanitized evidence records capture the stage, commit, test scope, counts, PASS/FAIL and remaining limitations.
- A stage may reuse or improve existing tests; an increasing test count is not a requirement.
- No stage is marked PASS without observed execution evidence. Pending host verification is explicitly PENDING.
- No known unexplained failure, test workaround, unresolved architectural defect, or hidden TODO may be carried into a CLOSED stage. Document the root cause and verify its fix; otherwise keep the stage OPEN.
- A passing test suite does not automatically close a stage when a known behavior remains unexplained.
- Keep runtime data and logs outside Git; commit only compact evidence summaries.

### 10. Official Documentation

- https://learn.microsoft.com/agent-framework/overview
- https://learn.microsoft.com/dotnet/core/testing/unit-testing-mstest-intro
- https://learn.microsoft.com/dotnet/core/testing/microsoft-testing-platform-intro

Documentation and package APIs must be verified
before implementation.

### 11. Repository Layout and Storage Policy

Repository root contains only repository-wide configuration files and
entry points (for example `global.json`, `Directory.Build.props`,
`.gitignore`, and a solution file). Application source code, tests,
backups, logs, and generated experiment outputs must not be stored as
loose files at the repository root.

Approved logical directories:
- `src/`: production source code and domain components.
- `tests/`: automated test projects and test fixtures.
- `benchmarks/`: performance benchmark projects, when needed.
- `docs/`: architecture, decisions, and small reviewable evidence records.
- `infra/`: infrastructure configuration and Docker definitions.
- `scripts/`: version-controlled development and maintenance scripts.
- `.github/`: GitHub automation and CI configuration.

Storage rules:
- Large historical datasets, experiment outputs, runtime logs, and
  backups are stored outside the repository working tree, in explicitly
  configured locations. They are not committed to Git.
- Temporary .NET `bin/` and `obj/` directories and `TestResults/`
  remain in their conventional locations and are ignored by Git.
  Moving these outputs outside the project is not a requirement.
- Only small, sanitized, reproducible evidence summaries and manifests
  may be versioned under `docs/evidence/`; no credentials, sensitive
  information, or large binary artifacts are committed.
- Runtime data paths must be configurable; code must not assume a
  developer-specific absolute path. Backup retention and recovery
  verification are separate acceptance gates and remain OPEN.
- Directories are created when needed, not as empty placeholders.

This section defines repository hygiene, not proof that external storage,
backup recovery, or the test infrastructure has been verified.

### 12. P0 — Unified Development Governance Controller (proposed implementation contract; OPEN)

Scope: **whole-project development governance**, separate from PHANTOM research-product State/Memory/Learning (SML) infrastructure. SML-01..06 implementation, existing PASS evidence and baselines remain unchanged. This P0 contract is an addition for governance; it does not close or reopen an SML gate. It becomes binding for subsequent implementation only when this change is reviewed and merged.

**Six simultaneous, complementary capabilities in ONE end-to-end lifecycle:**
1. **Dashboard** — GitHub Actions/Projects show actual stage execution, accepted/pending/blocked criteria, dependencies, alerts and last checkpoint. Dashboard is a read model, never independent acceptance authority.
2. **Evidence and progress** — discover existing work and stage criteria first; link code SHA, tests, artifacts, source provenance and evidence; reuse evidence only under verified scope and identical relevant inputs; do not infer PASS from an unexamined document.
3. **End-to-end phase execution** — deterministic contract: discover/preflight -> check baseline and dependencies -> plan -> authorized implementation -> build/integration/negative/regression tests -> evidence validation -> acceptance -> publish and durable checkpoint. Resume without duplicating externally visible side effects; cap retries. Model-backed coding worker and durable checkpoint backend are **NOT IMPLEMENTED**.
4. **Mandatory enforcement with actionable denials** — all accepted changes must pass governance acceptance. Every denial supplies `code, stage, reason, evidence, action, resume`; repair only within preauthorized scope. Branch rules/required checks must be tested as an actual merge barrier; GitHub Actions alone cannot prohibit direct pushes. This control is **NOT YET END-TO-END ENFORCED**.
5. **Fallible baseline governance** — baseline is versioned, reviewable and challengeable by official documentation, reproducible tests and evidence; routine conforming fixes require no baseline edits. A baseline contradiction is flagged and its affected change held pending reviewed amendment; never silently weaken tests to obtain PASS.
6. **Measured change impact and verified rollback** — before any accepted change, identify its intended improvement/maintenance goal, impacted components, matched pre-change measurements, immutable recovery reference, risk-adjusted metrics and maximum tolerated regressions. After the change, measure the same indicators with independently executed tests, including security, performance, scientific validity where relevant, and integration impact. Classify the comparison as IMPROVED / EQUIVALENT / REGRESSION / INCONCLUSIVE; a correct refactor can be EQUIVALENT, and an explicitly justified tradeoff may be acceptable if no pre-agreed safety bound is breached. REGRESSION or unsupported high-risk changes must be blocked; restore the known-good code/config/data state when required and verify the restoration, not merely reverse a Git commit. Persist provenance and comparison evidence. Neither checkpoint restoration nor passing tests alone demonstrates safe rollback or net benefit.

**Source-first / reuse-first admission (cross-cutting, not a seventh controller):** Before a material technical/architectural decision, inspect the repository's actual baseline, failure and retained evidence; consult the vendor's current primary documentation for the pinned implementation version; search existing supported APIs, tools, libraries and known patterns; compare reuse / extension / new build with tradeoffs and measurable outcomes. A new proprietary mechanism is permissible only after recording why an existing supported option does not meet the scope. Store a versioned decision record including official links, applicability, version, observed checks, competing options, risk and rollback. A link alone does not prove a version-compatible API; verify in build/tests or report OPEN. Source contradictions trigger scoped baseline review, not silent rewriting. Static schema checks are bootstrap admission only and cannot establish whether sources are factually correct or whether the full merge barrier works. The source-first evidence belongs to the six existing capabilities (discovery, baseline review, enforcement and impact), not a parallel orchestrator. Source-free material decisions must be blocked once per-change admission enforcement is implemented; until then that enforcement remains OPEN.\n\n**Single authority per fact:** baseline is versioned acceptance specification, Git SHA identifies implementation, CI run identifies test execution, verified evidence proves measured behavior, acceptance decision derives from all required criteria, and dashboard only projects that decision. Chat/agent opinions never override evidence. No ad-hoc alternative orchestrator or second status database.

**Architecture / support boundary:** Microsoft Agent Framework C# workflow/executors/state/checkpoint/HITL are the only orchestration foundation for the *governance workflow*; research workflow stays separately scoped under that same framework. GitHub Actions is CI/trigger and GitHub Projects is visualization, **not** a competing research orchestrator. Official support of framework primitives is not a guarantee of a turnkey governance product. Research SML checkpoints are not governance checkpoints.

**External engineering patterns are advisory, not dependencies:**
- Microsoft official docs: explicit workflow/executors, checkpoint/restore, state isolation and human approval. Check .NET package-version API compatibility before coding.
- Anthropic long-running agent harness: initializer + feature inventory, Git commits and durable progress record, fresh-session recovery, scoped incremental changes, automated end-to-end tests. Adapt patterns, not Claude/Anthropic SDK.
- Tsinghua ChatDev experiential co-learning: store attributed lessons and failure patterns separately from acceptance evidence; use experiences as suggestions subject to independent tests, **never** as automatic PASS or required new framework.

**Adoption/acceptance is a single integration proof:** one real open PHANTOM phase demonstrates existing-evidence reuse, minimal authorized edits, build/test, forced failure with structured denial and recovery, nonduplicated side effects after resume, automatic evidence/commit/PR publication, valid acceptance, and dashboard update. Negative tests must prove rejection of missing evidence, baseline weakening, unbounded regression, inconclusive high-risk changes, and a rollback that fails to restore expected behavior. An isolated integration test must exercise rollback and post-rollback verification. Until then this P0 gate is **OPEN**, not PASS.

**Operational limits:** no Azure dependency; no mandatory manual commits, evidence bookkeeping or fragmented test commands for normal runs. No autonomous change to critical security policy, accepted scientific metrics, or published baseline without separately reviewed authority. Never assume model use or hosted runners are unlimited/free. No release until entire project approval.

Detailed mapping, denial schema, and source-specific implementation templates: `docs/architecture/GOVERNANCE-CONTROLLER.md` and `docs/architecture/GOVERNANCE-CONTRACT.json`. The existing `scripts/check_repository_policy.py` must evolve as the repository governance admission guard; do not remove its proven layout rules or falsely present the present limited guard as full enforcement.
