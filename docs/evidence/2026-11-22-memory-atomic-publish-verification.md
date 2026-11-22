# PHANTOM | Atomic manifest publication verification

Date: 2026-11-22
Source: user-provided Ubuntu host test output
Status: HOST PASS for full infrastructure regression; overall SML stage OPEN

- Pulled main `75ce527..1c1b574`.
- Command: `dotnet test --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj --no-progress`.
- Host result: 44 total; 44 succeeded; 0 failed; 0 skipped; duration 3s 785ms.
- Includes `ResearchMemoryStoreTests.AtomicPublishIgnoresOrphanTempFilesAndRejectsDuplicate` added in `0d37c2c`, against atomic publication change `82ab4e1`.
- Scope: same-directory temporary manifest, flush and close, no-overwrite move, orphan temp not accepted as a final record, duplicate rejection and readback.
- Not verified: forced termination during actual `SaveAsync`, directory metadata persistence on power loss, hostile symlink protections, durable Agent Framework checkpoint resume, or trusted authorization.
- SML-02 and SML-03 remain OPEN.
