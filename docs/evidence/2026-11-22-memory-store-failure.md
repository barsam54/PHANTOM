# PHANTOM | Memory store host failure and correction

Date: 2026-11-22
Source: user-provided Ubuntu host output

- Revision tested: `c892d5c`.
- Command: `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj --no-progress`.
- Result: **FAIL**: 40 total, 39 succeeded, 1 failed, 0 skipped.
- Failed test: `ResearchMemoryStoreTests.RejectsInvalidAndUnrelatedExperimentIds`.
- Expected: `FileNotFoundException` for unknown experiment ID.
- Actual: `DirectoryNotFoundException` because the configured store directory did not yet exist.
- Root cause: `ReadAsync` directly opened a record path without normalizing a missing parent directory to the documented missing-record behavior.
- Fix: `d06771b` adds a missing-directory guard to `ReadAsync` and raises `FileNotFoundException` with the requested record path. Existing negative test exercises this case.
- **FIX PENDING HOST VERIFICATION**. No PASS claim for 40 tests or SML-03/04.
