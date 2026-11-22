# PHANTOM Infrastructure Status

Status: IN PROGRESS
Updated: 2026-11-22

## Verified evidence

- Ubuntu 26.04.1 LTS, amd64: PASS (reported host output).
- Docker 29.1.3 installed and daemon active: PASS. Privileged daemon query reported AppArmor, seccomp builtin, cgroupns, cgroups v2 and overlayfs; ordinary user socket access denied.
- Docker .NET SDK image pull and container smoke: PASS for startup and `dotnet --info` output. Image `mcr.microsoft.com/dotnet/sdk:10.0-noble`, SDK 10.0.404 and runtime 10.0.15 inside container. Restricted-container checks also PASS for observed controls (see `docs/evidence/2026-11-22-docker-container-smoke.md`).
- .NET SDK 10.0.115 installed: PASS.
- Git SSH transport and GitHub CLI authentication as barsam54: PASS (reported host output).
- Local MSTest execution via Microsoft.Testing.Platform: PASS, 18 succeeded / 0 failed / 0 skipped (user-reported 2026-11-22, 3.770 seconds); includes local evaluator, persisted structured evidence and independent deterministic rerun tests.
- Infrastructure test project committed and pushed: PASS, commit `eb883ddd9b99de345d63b14ebcc7399625acff13` (verified in GitHub).
- Repository Policy Guard: successful push runs for commits `eb883dd` (run 44978589860), `71be924` (44978869519), and `a3a7b99` (44978877041), as reported by GitHub CLI.
- Repository policy checker: five unit tests passed in earlier reported execution.

## Repository configuration

- `global.json`: SDK 10.0.115 with latestPatch roll-forward; Microsoft.Testing.Platform selected for dotnet test.
- `Directory.Build.props`: net10.0, nullable, implicit usings, warnings as errors, deterministic builds.
- `.gitignore`: excludes build outputs, test results, local secrets, local research datasets, and Python caches.
- `tests/Phantom.Infrastructure.Tests/`: MSTest project uses `EnableMSTestRunner=true` and `OutputType=Exe`.
- `Microsoft.Agents.AI` and `Microsoft.Agents.AI.Workflows` 1.28.0 restored and built successfully on .NET 10 (reported host output); package project committed as `e4dd2d8`.
- First two-executor Agent Framework workflow committed; 4 MSTest tests passed locally, including output and repeatability checks (reported host output).

## Open acceptance gates

- Repository-policy CI: earlier workflow commits reported PASS in GitHub CLI output (see `docs/architecture/GOVERNANCE.md`); latest commits NOT VERIFIED. .NET restore/build/test CI added as `.github/workflows/dotnet-build-test.yml`, execution result NOT VERIFIED.
- Test-project and referenced Agent Framework project local build: PASS (user-reported 2026-11-22). Repository-wide project inventory/solution build: NOT VERIFIED; no root solution is present.
- Microsoft Agent Framework two-executor workflow execution: PASS for deterministic smoke; LocalEvaluator integrated with actual workflow output and structured evidence: PASS for local tests. Model-backed agent and multi-agent evaluation: OPEN.
- Local Agent Framework evaluation: PASS, positive and negative assertions (user-reported 18-test run); broader agent evaluation remains OPEN.
- Docker restricted-container smoke: PASS (reported exit code 0; UID/GID 65534, zero effective capabilities, NoNewPrivs=1, no routes, 512 MiB memory, 0.5 CPU, 64 PIDs, root filesystem write denied). Ephemeral non-root .NET workspace with tmpfs and DOTNET_CLI_HOME: PASS (SDK 10.0.404, file round-trip, exit code 0). Evidence: `docs/evidence/2026-11-22-docker-container-smoke.md`. Explicit network-denial test, PHANTOM build/test inside container, untrusted-code isolation and automated evidence: OPEN.
- Deterministic repeatability and structured JSON evaluation evidence: PASS for local workflow tests, including independent runs and SHA-256 fingerprints. Scientific and cross-environment reproducibility: OPEN.
- Branch protection: BLOCKED by GitHub plan for this private repository (HTTP 403). Existing Actions detect violations but do not prevent direct pushes.

No overall software or architecture PASS is claimed. Agent Framework 1.28.0 is pinned. Outstanding: real cTrader research execution, data correctness/leakage tests, agent state/memory/learning, observability, full CI run verification, Docker execution of project/untrusted code, backup restoration, branch enforcement and cross-environment reproducibility.

## Official references

- https://learn.microsoft.com/en-us/agent-framework/get-started/workflows
- https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test
- https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-getting-started
