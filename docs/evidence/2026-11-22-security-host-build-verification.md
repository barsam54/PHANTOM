# Security host build and regression evidence

Date: 2026-11-22
Source: user-provided Ubuntu terminal output.
Checked out through commit: `120f81b` (prior fast-forward; exact local HEAD not printed).
- `dotnet build src/Phantom.ResearchSecurityHost/Phantom.ResearchSecurityHost.csproj`: **PASS**, 35.4s.
- `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj --no-progress`: **PASS**, 55 total / 55 succeeded / 0 failed / 0 skipped, 3.887s.
- Not verified: cross-UID runtime, socket access policy, key rotation and revocation, direct-store bypass resistance.
- SML-04 remains OPEN; no release.
