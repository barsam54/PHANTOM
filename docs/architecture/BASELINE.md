# PHANTOM
## Baseline Laboratory Architecture

Status: OPEN
Implementation: NOT STARTED

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

The baseline remains OPEN until evidence confirms:
1. A real Agent Framework workflow executes.
2. MSTest executes through Microsoft.Testing.Platform.
3. A real agent or workflow evaluation executes.
4. Results and evidence are recorded.
5. A deterministic test reproduces the same result.

### 10. Official Documentation

- https://learn.microsoft.com/agent-framework/overview
- https://learn.microsoft.com/dotnet/core/testing/unit-testing-mstest-intro
- https://learn.microsoft.com/dotnet/core/testing/microsoft-testing-platform-intro

Documentation and package APIs must be verified
before implementation.
