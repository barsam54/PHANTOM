# PHANTOM Governance and Denial Reporting

Status: PARTIAL; repository policy CI verified through 2026-11-22 reported runs; mandatory branch enforcement unavailable.
Updated: 2026-11-22

## Layers

1. Repository policy: `scripts/check_repository_policy.py` checks tracked files against the approved baseline and reports structured JSON violations. It is independent of Microsoft Agent Framework.
2. GitHub Actions: `.github/workflows/repository-policy.yml` runs the repository policy checker on pushes to `main`, pull requests, and manual dispatch. GitHub CLI output on 2026-11-22 confirmed successful runs for `e4dd2d8` (44979402746), `2e3b819` (44979477004), `db2f157` (44979481560), `8679c9e` (44979485823), and `4d4bfe3` (44979685436). Earlier output also confirmed `eb883dd` (44978589860). These are repository-policy checks, not proof of full .NET build/test CI.
3. Runtime control: `WorkflowAdmissionPolicy` checks request completeness and evidence-path prerequisites before starting the Agent Framework workflow; `WorkflowAdmissionException.Denial` exposes structured code, stage, reason, action and optional evidence. IMPLEMENTED; new host tests PENDING. This is a narrow admission guard, not complete runtime policy enforcement.

## Denial format

Failures must report: `code`, `stage`, `reason`, `action`, and, when available, `evidence`.

## Enforcement limitations

- Branch protection API returned HTTP 403 for the private repository: GitHub requires an eligible paid plan or a public repository for that feature.
- The repository remains private. No upgrade or public visibility change is planned for this stage.
- GitHub Actions detects violations after a push; it cannot guarantee prevention of direct pushes without enforced branch rules.
- No additional repository-policy controller or local Git hook is required by the current decision.

## .NET CI verification

- `.github/workflows/dotnet-build-test.yml`: three push runs reported successful by `gh run list` on 2026-11-22: `44986930555`, `44986936161`, `44986944911`.
- Evidence: `docs/evidence/2026-11-22-ci-verification.md`.
- This is successful workflow status, not branch protection enforcement or proof of full repository-wide test coverage.

## Open verification

- Verify GitHub Actions result for new commits after this checkpoint; earlier successful runs do not establish future commit status.
- Test structured denial reporting with an invalid change in an isolated branch when needed.
- Verify the new admission tests on host; expand admission policy to data availability, research permissions and isolated execution when those components exist.

## Microsoft references

- https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/
- https://learn.microsoft.com/en-us/agent-framework/workflows/workflows
- https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop

## GitHub reference

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
