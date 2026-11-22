# PHANTOM Governance and Denial Reporting

Status: PARTIAL; enforcement NOT VERIFIED.

## Layers
1. Repository policy: `scripts/repository_policy.py` checks tracked files against the approved baseline and returns structured JSON failures. It is independent of Microsoft Agent Framework.
2. Runtime control: future Microsoft Agent Framework workflow executors and conditional routing will check prerequisites and return structured denial reasons. NOT IMPLEMENTED.

## Denial format
Every failure must report: `code`, `stage`, `reason`, `action`, and when available `evidence`.

## Enforcement gaps
The repository policy script was committed but its GitHub Actions workflow could not be created through the connected GitHub API (HTTP 422). It has not been executed or verified.
No branch ruleset has been enabled. A CI check without a required branch ruleset does not prevent direct pushes. The requested prevention guarantee is NOT MET.

## Proposed protections
- Require pull requests into main.
- Require the repository-policy status check.
- Block force pushes and branch deletion.
- Restrict bypass where supported.
- Verify denial behavior with a deliberately invalid change on a test branch.

## Microsoft references
- https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/
- https://learn.microsoft.com/en-us/agent-framework/workflows/workflows
- https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop

## GitHub reference
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
