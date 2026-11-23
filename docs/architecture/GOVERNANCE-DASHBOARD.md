# PHANTOM | Native GitHub Governance Dashboard

**GOV-P0: OPEN.** This is a read-only dashboard; not an alternative controller.

## Open the running dashboard

1. [Repository Policy Guard - GitHub Actions](https://github.com/barsam54/PHANTOM/actions/workflows/repository-policy.yml)
2. Open the latest successful run for PR #1 / branch `governance/p0-unified-controller-contract`.
3. Select the job **Validate repository layout and explain violations** and its **Summary**.

The summary shows a six-capability acceptance bar and table, proof still
missing for each capability, current revision and contract digest, historical
merge-denial proof, checkpoint/execution limitations, and remaining blockers.
It is rendered by the existing `scripts/governance_inventory.py` through
`GITHUB_STEP_SUMMARY`, the officially supported GitHub Actions summary
mechanism. The JSON snapshot is available as the existing
`governance-inventory` Actions artifact.

**No acceptance is invented:** a completed job is distinct from scientific
acceptance; a discovered evidence file is not verified evidence. All six
contract capabilities currently remain OPEN (0/6 accepted). Pending/blocked
items are visible even on green CI.

## GitHub Projects linkage

GitHub Projects supports native tables, boards, Insights charts and workflow
automations. To avoid maintaining a second authority, any future Projects
board must project verified run manifests and contract decisions; it must
never mark a capability PASS on the basis of a manually changed card.

**Projects sync: NOT CONFIGURED / OPEN.** The available connected GitHub
app does not expose writable Projects management actions. Do not claim an
operational Projects board or a synchronized chart.

## Official references

- GitHub Actions job summaries:
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands
- GitHub Projects native boards/charts:
  https://docs.github.com/en/issues/planning-and-tracking-with-projects
- GitHub Projects API:
  https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects

Source of truth:
`docs/architecture/GOVERNANCE-CONTRACT.json`.
This view is informational and cannot approve an OPEN capability.
