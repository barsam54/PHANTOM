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
