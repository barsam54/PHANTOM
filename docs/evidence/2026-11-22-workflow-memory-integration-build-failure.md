# PHANTOM | Workflow-to-memory integration build failure

Date: 2026-11-22
Status: FIX COMMITTED; HOST RE-VERIFICATION PENDING

- User-reported host run after pulling `e2dbcdf` failed during test-project build.
- Diagnostic: `WorkflowMemoryIntegrationTests.cs(39,13): error MSTEST0017` (expected/actual argument order detected as swapped).
- Root cause: `Assert.AreEqual(actual, await File.ReadAllTextAsync(...))` passed a variable as the expected argument while the file read was the actual value.
- Fix: `378cfc9` uses literal expected `"MOTNAHP"` as the first argument and file content as actual.
- No integration test executed in this failed build; no PASS is claimed.
- Required verification: rerun full infrastructure suite on Ubuntu host, expected 43 tests.
