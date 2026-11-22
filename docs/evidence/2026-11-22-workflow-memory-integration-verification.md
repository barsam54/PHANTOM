# PHANTOM | Real workflow-to-memory integration verification

Date: 2026-11-22
Source: user-provided Ubuntu host output
Status: HOST PASS for the deterministic Agent Framework-to-memory integration test; overall SML stage OPEN

- Full infrastructure suite: 43 total, 43 succeeded, 0 failed, 0 skipped.
- Duration: 2s 015ms.
- Includes `WorkflowMemoryIntegrationTests.RealAgentFrameworkWorkflowOutputPersistsAndRestoresWithScopedMemory` (`a562ffa`).
- Initial build failed with MSTEST0017; corrected in `378cfc9`; root cause documented in `docs/evidence/2026-11-22-workflow-memory-integration-build-failure.md`.
- Scope: actual two-executor Microsoft Agent Framework workflow output, local evidence persistence, memory manifest readback, experiment scope rejection, evidence tampering rejection.
- Not verified: process termination/restart recovery, authenticated authorization, model-backed scientific evaluation, external-worker isolation, or held-out learning.
- SML-06 and overall baseline remain OPEN.
