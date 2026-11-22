# PHANTOM | Workflow Observability Verification

Date: 2026-11-22
Scope: deterministic local workflow instrumentation and MSTest regression
Evidence source: user-supplied Ubuntu terminal output; GitHub code inspection
Status: TESTS PASS; broader observability stage OPEN

## Implementation

- Production source: `src/Phantom.AgentFramework/FirstWorkflow.cs`.
- Tests: `tests/Phantom.Infrastructure.Tests/WorkflowObservabilityTests.cs`.
- Instrumentation: one `phantom.experiment.evaluate` Activity per invocation, with experiment-specific metadata and success/error status; no input/output payload in tags.
- Trace assertion checks exactly one matching Activity per experiment ID; implementation/test change commit: `3ee9831796e93206743504e5a7f10043f4c5365c`.

## Observed results

| Execution | Runs | Tests per run | Total passed | Failed |
| --- | ---: | ---: | ---: | ---: |
| Full infrastructure suite, normal execution after cardinality change | 1 | 24 | 24 | 0 |
| Full infrastructure suite with serial-configured runsettings | 20 | 24 | 480 | 0 |
| Isolated `WorkflowObservabilityTests`, default settings | 20 | 2 | 40 | 0 |

These are separately reported runs; the 20 isolated runs were shown in full in the user's terminal output. The 20 serial-configured runs all reported PASS; the terminal output did not independently display the effective worker count.

## Incident, not attributed

- A separate earlier full-suite run terminated at repetition 10 with `Fatal error. Internal CLR error. (0x80131506)`, exit code 134, before any assertion result.
- Environment reported: Ubuntu 26.04 x64, Microsoft.NETCore.App 10.0.15, MSTest 4.0.1; `[assembly: Parallelize(Scope = ExecutionScope.MethodLevel)]` is present in `MSTestSettings.cs`.
- The earlier 9 full-suite repetitions passed before this crash.
- The incident was not reproduced in the subsequent 20 serial-configured full-suite runs or 20 isolated observability runs.
- Cause remains UNKNOWN: no demonstrated production workflow defect, test race, or runtime defect. No permanent parallelization change or speculative workaround is justified by this evidence.
- If it recurs, collect test-host diagnostics and investigate against the specific reproduction.

## Acceptance boundary

- PASS: observed deterministic workflow tracing assertions, negative-path coverage, and existing 24-test regression suite in the successful runs.
- OPEN: exporter/model-backed observability and broader baseline acceptance.
- Do not treat the isolated CLR incident as a confirmed architectural defect or claim its root cause was fixed.
- No release or overall architecture PASS is authorized by this record.
