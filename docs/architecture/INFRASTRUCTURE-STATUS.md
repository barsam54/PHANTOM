# PHANTOM Infrastructure Status

Status: IN PROGRESS
Updated: 2026-11-22

## Verified on user's Ubuntu host (reported command output)

- Ubuntu 26.04.1 LTS, amd64: PASS
- Docker 29.1.3 installed: PASS (daemon execution not yet tested)
- .NET SDK 10.0.115 installed: PASS
- Git branch main synchronized with origin/main at d3608d3: PASS at last inspection
- Git SSH access via ssh.github.com:443: PASS

## Repository configuration (committed, not execution-verified)

- global.json: SDK 10.0.115 with latestPatch roll-forward; MTP selected for dotnet test.
- Directory.Build.props: net10.0, nullable, implicit usings, warnings as errors, deterministic builds.
- .gitignore: excludes build outputs, test results, local secrets, and local research datasets.

## Open acceptance gates

- Local repository sync after new remote commits: OPEN
- dotnet restore/build: NOT RUN
- MSTest through MTP: NOT RUN
- Microsoft Agent Framework workflow: NOT RUN
- Agent/workflow evaluation: NOT RUN
- Docker daemon and container smoke test: NOT RUN
- Evidence-producing repeatability test: NOT RUN

No software test PASS is claimed. No NuGet package version for Microsoft Agent Framework is pinned until verified and restored.

## Official references

- https://learn.microsoft.com/en-us/agent-framework/get-started/workflows
- https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test
- https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-getting-started
