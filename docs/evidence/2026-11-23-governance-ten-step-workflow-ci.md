# GOV-P0 | Ten-step Microsoft Agent Framework governance workflow smoke
Date (UTC): 2026-11-22
Branch: `governance/p0-unified-controller-contract`
Verified source SHA: `7c211c5149f4c35fcb9e4878d669a2ed08ac293a`
Evidence class: **CI run verified; limited read-only governance workflow scope**
Overall gate: **OPEN** (not accepted).

## Execution evidence
- `Repository Policy Guard`: SUCCESS, run **45084947997**; contract/policy negative tests and ten-step Python diagnostic.
- `PHANTOM .NET Build and Tests`: SUCCESS, run **45084948007**; restored and built `tests/Phantom.Infrastructure.Tests` with its referenced `Phantom.AgentFramework` package, then executed MSTest via Microsoft.Testing.Platform.
- C# framework workflow `GovernancePhaseWorkflow.RunAsync` is exercised by `GovernancePhaseWorkflowTests`: an ordered chain of ten `Microsoft.Agents.AI.Workflows` executors with structured reasons, actions and resume references. Tests require `GOV-P0=OPEN` and check missing/invalid inputs and absent executors.
- Earlier run **45084871270** failed in MSTEST0037 for a test assertion. The issue was corrected to use `Assert.HasCount` without weakening MSTest rules; retest **45084948007** succeeded.
- Vendor API references: https://learn.microsoft.com/en-us/agent-framework/workflows/workflows and https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints.

## Exact scope and exclusions
- Verified: ordered C# framework workflow and read-only diagnostic status reporting, guarded policy contract and test execution.
- **Not verified or implemented:** independent authorized code-writing worker, phase-specific build/evaluation actually initiated by the C# governance workflow, full provenance validation, automatic evidence commit/PR by a stage runner, GitHub Projects status sync, durable governance checkpoint, enforced branch admission, measured before/after improvement, rollback and post-rollback integrity.
- The ten steps report OPEN/NOT_IMPLEMENTED/BLOCKED where appropriate; passing infrastructure tests does **not** mean ten production operations were completed.
- SML product memory/learning gates are separate. No release; no change to accepted SML-04 operational evidence.

## Integrity and limitations
This is a sanitized source-controlled index of official GitHub Actions run IDs and commit scope, not a fabricated runtime log. Check each run at the pinned SHA before reuse. New evidence is required for the remaining full end-to-end acceptance criteria.
