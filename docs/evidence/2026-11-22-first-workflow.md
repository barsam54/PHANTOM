# PHANTOM | First Workflow Checkpoint

Date: 2026-11-22
Status: PASS for initial deterministic workflow smoke test; specialized agent/workflow evaluation OPEN.

## Experiment identity
- ID: PHANTOM-WF-SMOKE-20261122-001
- Repository: barsam54/PHANTOM
- Tested repository revision: `4d4bfe37392c283f1ff29be393bc5a9c174d16d6` (reported fast-forward to `4d4bfe3` before execution)
- Framework: Microsoft.Agents.AI 1.28.0; Microsoft.Agents.AI.Workflows 1.28.0
- Runtime: .NET 10, Microsoft.Testing.Platform via MSTest
- Environment: local Ubuntu x64, reported terminal output

## Input and execution configuration
- Workflow: `src/Phantom.AgentFramework/FirstWorkflow.cs`
- Two executors: uppercase invariant, then reverse; `WorkflowBuilder`, `InProcessExecution.RunAsync`.
- Representative input: `Hello, World!`
- Expected output: `!DLROW ,OLLEH`
- Deterministic repeat input: `PHANTOM`
- Expected repeat output: `MOTNAHP`
- No cloud provider or external model used.

## User-reported execution results
- `dotnet restore src/Phantom.AgentFramework/Phantom.AgentFramework.csproj`: PASS.
- `dotnet build src/Phantom.AgentFramework/Phantom.AgentFramework.csproj --no-restore --warnaserror`: PASS.
- `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj`: 4 succeeded, 0 failed, 0 skipped; duration 2.497s.
- `python3 -m unittest discover -s tests/policy -p 'test_*.py' -v`: 5 succeeded.
- `python3 scripts/check_repository_policy.py`: PASS, 17 checked files, zero violations.
- `git status --short`: empty (clean).
- Five latest GitHub Actions policy runs shown as successful, including run 44979685436 for the status-document commit.

## Acceptance boundary
- PASS: initial workflow execution, expected-output test, repeatability smoke test, local build and policy tests.
- OPEN: Agent Framework's dedicated agent/workflow evaluation API execution; persisted machine-generated experiment manifest; independent rerun; research-domain validation.
- This evidence is a summary of the user's terminal output, not a captured machine-generated test artifact.
