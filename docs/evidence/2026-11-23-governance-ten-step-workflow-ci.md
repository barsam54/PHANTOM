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

## Addendum 2026-11-23: conservative criterion-scoped reuse admission

- Observed successful policy CI [run 45123226740](https://github.com/barsam54/PHANTOM/actions/runs/45123226740) and successful .NET CI [run 45123226675](https://github.com/barsam54/PHANTOM/actions/runs/45123226675), both at PR head `2d9b99a331ed8d683e4401370f169c3da3f713b2`.
- Added `scripts/check_governance_reuse_eligibility.py` and `tests/policy/test_governance_reuse_eligibility.py`: only an independently checked historical proof, matching criterion ID and **identical complete Git tree** can be declared `REUSABLE`. Any difference must be `BLOCKED` with `REUSE_INPUT_TREE_CHANGED`.
- Policy CI queried GitHub's commit/tree readback for the historical .NET evidence and current checkout. Actual result: **BLOCKED / REUSE_INPUT_TREE_CHANGED**, as expected for changed repository inputs. The negative assertion passed; no historical PASS was promoted to the new revision.
- Positive tests cover distinct commits with identical trees; negatives cover changed trees, wrong criterion, forged/missing proof, incomplete commit identity, and missing tree data. The test cases are not proof that actual GitHub runs with identical trees occurred.
- [Reuse eligibility artifact (14794472790)](https://github.com/barsam54/PHANTOM/actions/runs/45123226740) captures the provider-attested comparison.

**Scope and remaining limitations:** This intentionally over-restrictive full-tree check may deny reuse for changes irrelevant to the test. It does not yet derive minimal per-criterion dependency fingerprints; the conservative denial is safer than applying mismatched evidence. Neither the standalone check nor historical receipts certify GOV-P0 acceptance or the full end-to-end phase. All six capability acceptance states remain OPEN until complete stage-to-criterion mapping and approved acceptance are demonstrated.

## Addendum 2026-11-23: six-criterion evidence traceability matrix

- Full-PR-head SHA `eb749da0bfe8ce01b4b811f9d7ba681fdb93b80d`: [Repository Policy Guard run 45123693245](https://github.com/barsam54/PHANTOM/actions/runs/45123693245) and [.NET run 45123693284](https://github.com/barsam54/PHANTOM/actions/runs/45123693284) both concluded **success**.
- A read-only `scripts/governance_criteria_matrix.py` now derives **all six** GOV-P0 acceptance criteria from the versioned governance contract and requires two authentic scoped historical receipts and the .NET reuse eligibility decision.
- GitHub policy CI's step `Build six-criterion evidence traceability matrix` succeeded. It emitted an independent `governance-criteria-matrix` Artifact with six pending acceptance criteria, two historical CI proofs and **zero** capability-level acceptances.
- Negative tests reject missing/duplicate criteria, forged PASS, unverified/off-criterion CI evidence, missing reuse decision and contradictory reuse claim. The dashboard remains a read-only projection; neither a list of six nor successful CI grants GOV-P0 PASS.
- Outstanding single-integration acceptance is **not** demonstrated: full authorized phase run, reproducible forced failure/resume, nonduplicated external side effects, automatic commit/PR and Projects update, paired impact evaluation, rollback and independent post-rollback verification.

This artifact is a criterion-to-evidence **coverage inventory**, not a final acceptance verdict. The versioned contract and full GOV-P0 remain OPEN.

## Addendum 2026-11-23: cross-workflow exact-checkout pairing

- Audit of the prior evidence matrix exposed a critical admission weakness: independently valid Policy and .NET receipts could belong to **different** PR head commits or synthetic merge checkouts. Counting both as one phase proof was unsound.
- Added `scripts/verify_governance_evidence_pair.py` and negative tests, bound the .NET historical selection to the **same historical PR head** selected by Policy, and made `scripts/governance_criteria_matrix.py` refuse any mismatched pair. The matrix now records `historical_proofs_same_checkout_verified`.
- **Observed successful live proof:** [Repository Policy Guard run 45125785953](https://github.com/barsam54/PHANTOM/actions/runs/45125785953) and [.NET run 45125785793](https://github.com/barsam54/PHANTOM/actions/runs/45125785793) both succeeded at head `602033f2efd6507bc7df50bb494c9db5bd707ad8`.
- The policy run downloaded and independently verified prior [Policy run 45124663986](https://github.com/barsam54/PHANTOM/actions/runs/45124663986) and [.NET run 45124663993](https://github.com/barsam54/PHANTOM/actions/runs/45124663993), both at original head `ae062f50254a755206338ba3d5ffc80e5cfc4805`. Exact synthetic checkout SHA matched. The pairing step reported **`PAIR_CHECK_OK / IDENTICAL_PR_HEAD_AND_CHECKOUT`**. This is historical provenance binding, **not** proof that the current commit has the same input tree.
- [Paired evidence artifact 14795123999](https://github.com/barsam54/PHANTOM/actions/runs/45125785953) was stored by GitHub with provider SHA256 `d88ae33f6e913c2b733cf3a665ed97408be17d89aef7e18f423e62246fd2ca5c`. [Six-criterion matrix artifact 14795477186](https://github.com/barsam54/PHANTOM/actions/runs/45125785953) has provider SHA256 `3aafbe340ab17be891414e77ecba580aa84d2de85d4151645a79a5fed4c80d39`.
- Tests explicitly reject mismatched heads, mismatched checkouts, colliding run IDs, forged provider scope and false acceptance. No current-code PASS was inherited from historical evidence.
- **Blocking dependency for full capability 2 acceptance:** `GovernancePhaseWorkflow` is currently a ten-step **read-only** Microsoft Agent Framework chain. It does not execute an authorized real phase, consume these independent receipts as verified phase-scoped acceptance evidence, publish the resulting accepted decision or prove side-effect-safe recovery. Under Baseline §12's required single integration proof, **capability 2 and GOV-P0 stay OPEN**. This is a concrete orchestration/acceptance dependency, not a missing unit test. Do not downgrade the baseline criteria to make the capability look accepted.

No merge, release, model self-approval, or baseline amendment was performed.

## Addendum 2026-11-23: consolidated evidence validation entrypoint

- Three former GitHub Actions validation stages (independent Policy/.NET checkout pairing, full-tree reuse admission and six-criterion matrix) are now called **once in order** by `scripts/governance_evidence_pipeline.py`. Existing specialized modules remain as independent pure validators; no second governance orchestrator or second acceptance state database was introduced.
- The entrypoint processes already provider-attested historical receipts, checks both receipts refer to exactly one PR checkout, attests both Git trees through GitHub, denies reuse on changed input trees, then constructs the full six-criterion matrix. Denials block the pipeline unless the only denial is a correctly verified changed-tree reuse refusal. No artifact is accepted for a new source revision merely because old tests succeeded.
- Observed on [Repository Policy Guard run 45126843648](https://github.com/barsam54/PHANTOM/actions/runs/45126843648): **success** at PR head `e8d9892412bf089ea3d463cacb602bdf2429a459`. The unit suite reported **136 tests, OK**. The unified step emitted `UNIFIED_EVIDENCE_PIPELINE: VERIFIED_SCOPE_ONLY; GOV-P0: OPEN` with pairing `PAIR_CHECK_OK` and refusal `REUSE_INPUT_TREE_CHANGED` for old .NET evidence. Matching [.NET run 45126843612](https://github.com/barsam54/PHANTOM/actions/runs/45126843612) also succeeded.
- The one `governance-evidence-pipeline` artifact stores the consolidated status and underlying distinct receipts for audit/readback, instead of multiplying competing acceptance statuses.
- Honest acceptance scope: `VERIFIED_SCOPE_ONLY` is a pass for the **audit procedure**, not a capability PASS. The current Microsoft Agent Framework governance workflow still cannot consume verified phase-scoped evidence, complete an authorized real phase, or grant approved acceptance. Full capability #2 and GOV-P0 remain **OPEN**.

No merge, release, baseline weakening, approval by model or alternate workflow executor occurred.
