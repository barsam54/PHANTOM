# PHANTOM Gate 4 / Gate 5 verification protocol
Date: 2026-11-22
Status: PASS — LOCAL INFRASTRUCTURE SCOPE (user-reported host execution)

## Baseline mapping
- Gate 4: structured JSON evidence contains experiment ID, code version, input, execution configuration, verdict, evidence path, evaluator identity/version, actual/expected output, evaluator pass/fail counts and a reproducibility fingerprint.
- Gate 5: two independent real Agent Framework workflow executions with distinct experiment IDs and external directories must yield identical evaluation details and SHA-256 fingerprints. Changing expected output must produce FAIL and a different fingerprint.

## Implementation
- `ExperimentResult.Evaluation` is optional for legacy records, populated by `FirstWorkflow.RunWithEvidenceAsync`.
- `ExperimentEvidenceStore` writes the structured record with CreateNew; no overwriting.
- Fingerprint is SHA-256 of canonical JSON of code version, input, configuration, actual and expected outputs, evaluator counts/verdict and exact-match verdict. It deliberately excludes experiment ID and evidence location.
- `EvaluationReproducibilityTests` covers persisted success, persisted failure, independent repeatability and changed expected output.
- This does not establish scientific repeatability across historical datasets, processes, hosts or package upgrades. No trading validity is implied.

## Acceptance
Host evidence reported 2026-11-22 after commit 5df6fb5: project build succeeded in 1.5s; MSTest run passed 18/18, failed 0, skipped 0, duration 3.770s. Gates 4 and 5 PASS for the implemented local infrastructure acceptance tests. Scientific reproducibility across datasets, environments and production strategies remains OPEN; full PHANTOM baseline remains OPEN.
