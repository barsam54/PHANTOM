# PHANTOM | Research security boundary regression

Date: 2026-11-22
Status: HOST PASS for implemented security boundary code; SML-04 OPEN

- Source: user-provided Ubuntu terminal output.
- Host pulled main `9983395..514e286`.
- Command: `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj --no-progress`.
- Result: 51 total, 51 succeeded, 0 failed, 0 skipped, duration 1s 926ms.
- Coverage includes identity-scoped short-lived grant issuer, Unix key-file permission checks and storage directory permission checks.
- Prior build failures: CA1416 Unix platform analyzer and MSTEST0037 assertion analyzer; both corrected and host regression now passes.
- **Not verified:** external authentication provider, trusted process boundary, key rotation/revocation service, actual deployed filesystem isolation, cross-UID denial. Overall SML-04 OPEN. No release.
