# PHANTOM Governance and Denial Reporting

Status: PARTIAL; repository policy CI verified on earlier commits; mandatory branch enforcement unavailable.
Updated: 2026-11-22

## Layers

1. Repository policy: `scripts/check_repository_policy.py` checks tracked files against the approved baseline and reports structured JSON violations. It is independent of Microsoft Agent Framework.
2. GitHub Actions: `.github/workflows/repository-policy.yml` runs the repository policy checker on pushes to `main`, pull requests, and manual dispatch. Six earlier push runs were reported successful by GitHub CLI on 2026-11-22. A run for commit `eb883dd` was not found using `gh run list --commit eb883dd`; its CI status remains NOT VERIFIED.
3. Runtime control: future Microsoft Agent Framework workflows will validate prerequisites and report structured denial reasons. NOT IMPLEMENTED.

## Denial format

Failures must report: `code`, `stage`, `reason`, `action`, and, when available, `evidence`.

## Enforcement limitations

- Branch protection API returned HTTP 403 for the private repository: GitHub requires an eligible paid plan or a public repository for that feature.
- The repository remains private. No upgrade or public visibility change is planned for this stage.
- GitHub Actions detects violations after a push; it cannot guarantee prevention of direct pushes without enforced branch rules.
- No additional repository-policy controller or local Git hook is required by the current decision.

## Open verification

- Verify GitHub Actions result for the latest commit, rather than relying on the latest listed run if it predates the push.
- Test structured denial reporting with an invalid change in an isolated branch when needed.
- Implement and evaluate runtime prerequisite checks using Microsoft Agent Framework.

## Microsoft references

- https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/
- https://learn.microsoft.com/en-us/agent-framework/workflows/workflows
- https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop

## GitHub reference

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
