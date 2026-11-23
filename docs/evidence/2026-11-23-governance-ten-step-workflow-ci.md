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

## Addendum 2026-11-23: independent-run evidence readback and scoped reuse

**Observed proof on branch (not a release or complete GOV-P0 acceptance):**
- New verifier: `scripts/verify_prior_governance_evidence.py`, plus negative tests `tests/policy/test_verify_prior_governance_evidence.py`.
- Successful policy CI run: [45120621916](https://github.com/barsam54/PHANTOM/actions/runs/45120621916), PR head `f55e08be297f4b8a13e9c8a4d614db14a194f234`; corresponding [.NET run 45120621908](https://github.com/barsam54/PHANTOM/actions/runs/45120621908) also succeeded.
- The policy CI run selected **prior independently completed success run 45120604657** (PR head `dfd1638b7a499fefc1e5ff2ca1a4bb0c5d768a25`) and downloaded its `governance-inventory` artifact with official `actions/download-artifact@v4` using `run-id` and read-scoped GitHub token.
- Prior artifact ID `14793183856`; provider archive digest `sha256:afc9b2fd9773dcc0223fae01a933f2c04fa8cc89569d04ea687b07ca7e5f7412`; validated historical merge checkout `b4f785d236d71a3cd5cc7c0ee182df9a7077d1e0`, tied to the prior PR head by GitHub commit parent readback.
- The two **independent verifier invocations** both returned `CHECK_OK` with equal deterministic repacked report digest `5da8451b06a0cb44e77c1d56b1a1b18fbf874618a840944424a49142f28ba392`. Reports were persisted as [artifact `governance-cross-run-reuse` (14792898711)](https://github.com/barsam54/PHANTOM/actions/runs/45120621916).
- Negative tests reject forged PASS, mismatched historical run/head/merge parents, changed baseline digest, missing report/artifact, failed prior job and wrong criterion. No old build or test job was restarted by the verifier.

**Scope / explicit exclusions:** The original GitHub ZIP archive digest is provider metadata; `actions/download-artifact@v4` transports the extracted content. Python validates a newly **repacked** deterministic ZIP; its digest is not the original archive digest, and the Python step does **not** claim independent byte-level verification of the provider ZIP. The verifier proves historical `governance.policy_ci` readback and reuse at the original checkout SHA. It does **not** approve the current source revision, certify all other stage criteria, show live GitHub Projects sync, or accept GOV-P0. Whole-governance and capability-level acceptance remains **OPEN** under the existing versioned contract.

**Failure/recovery provenance:** Earlier cross-run verification attempts were blocked by 401 at the direct archive API endpoint and then by time-dependent ZIP metadata causing two valid readbacks to yield different hashes; switching to the documented official cross-run `download-artifact` action and deterministic `ZipInfo` timestamps resolved these observed failures. Neither was silently relabeled PASS.

## Addendum 2026-11-23: .NET test evidence readback in independent run

Evidence scope: `governance.dotnet_ci` only; prior-run results are tied to their original checkout, **not** automatically applicable to current code or all stages.

- [Policy run 45122587879](https://github.com/barsam54/PHANTOM/actions/runs/45122587879): SUCCESS at PR head `885b079db9048c55d0f3b273937885ea48d8a4f6`. Its steps selected an independent successful earlier .NET run, downloaded its Artifact and validated it. The complete [corresponding .NET run 45122587866](https://github.com/barsam54/PHANTOM/actions/runs/45122587866) is also SUCCESS.
- Selected earlier .NET run: [45122508879](https://github.com/barsam54/PHANTOM/actions/runs/45122508879), head SHA `99939104a76cc82105fc70233cdcab0ade474f1f`.
- Pinned test log SHA-256 reported by the cross-run verifier: `1f6cf25129fb0c02300424f5b98a763525528420c8ac56a262652eb6f1d83848`.
- Current workflow now publishes `governance-dotnet-test-evidence` containing the real Microsoft.Testing.Platform stdout/stderr log and a hash-bound receipt. Independent readback checks GitHub run/job/step status, artifact provenance, PR merge checkout parent, baseline/contract SHA-256, and matching log hash/byte count. Negative unit tests reject a forged PASS, mismatched log, wrong lineage, missing file, failed test step, and expired artifact.
- The readback and prior policy-run reuse both passed in run 45122587879; the validator did not restart the prior run or call `dotnet test`.
- Stored output: [governance-cross-run-dotnet-evidence artifact 14794466156](https://github.com/barsam54/PHANTOM/actions/runs/45122587879).

**Limitations:** GitHub's original archive checksum is attested as provider artifact metadata and transferred by the official download action; the Python readback does not independently hash original ZIP bytes. A successful historical .NET test record covers only the test scope stated here. Historical success cannot prove current SHA equivalence or completed end-to-end governance. Capability #2 and full GOV-P0 remain **OPEN** until the full criteria-to-implementation mapping and acceptance integration are independently verified.
