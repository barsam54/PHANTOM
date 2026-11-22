# SML-04 security host hardening verification

Date: 2026-11-22
Evidence: user-provided Ubuntu terminal output after `f3d5fdb`.
- `dotnet build src/Phantom.ResearchSecurityHost/Phantom.ResearchSecurityHost.csproj`: PASS, 2.2s.
- `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj --no-progress`: PASS, 57/57, failed 0, skipped 0, duration 3.817s.
- Scope: regression tests including key-replacement invalidation, root refusal and request timeout code compilation.
- Subsequent malformed-cutoff denial fix and test: PENDING host verification.
- Cross-UID deployed process, socket group and filesystem isolation and actual key restart rotation: NOT VERIFIED. SML-04 OPEN; no release.
