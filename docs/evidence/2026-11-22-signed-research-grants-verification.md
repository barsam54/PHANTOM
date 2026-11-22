# PHANTOM | Signed research grants host verification

Date: 2026-11-22
Status: HOST PASS for signed-grant implementation; SML-04 OPEN

- Source: user-provided Ubuntu terminal output.
- Pulled main `6d6c842..302d0c2`.
- Production code: `src/Phantom.AgentFramework/SignedResearchMemoryAccess.cs` (`c5da490`).
- Regression: `tests/Phantom.Infrastructure.Tests/SignedResearchMemoryAccessTests.cs` (`6f17af5`).
- Command: `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj --no-progress`.
- Result: 49 total; 49 succeeded; 0 failed; 0 skipped; duration 2s 135ms.
- Scope: valid HMAC-SHA256 scoped grant, tampering, expiry, wrong key, wrong experiment, cutoff, and UTC checks.
- Not demonstrated: secure key custody and rotation, trusted host authentication/issuance boundary, untrusted-process isolation, OS file permissions. SML-04 and overall stage OPEN. No release.
