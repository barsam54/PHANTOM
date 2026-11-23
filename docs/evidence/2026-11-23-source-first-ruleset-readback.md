# GOV-P0 | Live official-source and branch-ruleset readback

Status: **OBSERVED / PARTIAL**, not whole-project acceptance.
Observation date: 2026-11-23.
Repository: `barsam54/PHANTOM`; PR: #1; branch: `governance/p0-unified-controller-contract`.

## Official-source validation on existing PR head

The repository ALREADY implements a live fail-closed text verification pass in
`scripts/verify_official_sources.py` and tests in
`tests/policy/test_live_source_verification.py`.
The workflow `.github/workflows/repository-policy.yml` requires this step,
before PR-diff admission. The .NET workflow also requires it before
installation and build. Sources are restricted to the exact official hosts
listed in `GOVERNANCE-CONTRACT.json`, redirects are checked, downloads are
bounded and each record must declare its expected terms.

**Verified CI evidence at commit `6f00087d6fc1f5f065db4fd29e674eef0fcd1e3b`:**
- Policy run `45090754546`: SUCCESS; step
  `Live-verify official sources and declared technical claims`: SUCCESS.
- .NET run `45090754541`: SUCCESS; identical live-source verification
  step SUCCESS; subsequent build and tests SUCCESS.

Interpretation: this proves live retrieval and occurrence of declared text.
It does **not** independently demonstrate that technical interpretations,
pinned NuGet APIs and intended capabilities are all correct.
The Ollama .NET provider divergence is explicitly recorded in
`SOURCE-FIRST-DECISION.json`; it remains a review item, not proof of parity.

## Main branch ruleset readback

Read-only GitHub REST retrieval via the connected GitHub app:

- Repository `GET /repos/barsam54/PHANTOM`: `visibility=public`,
  `private=false`, `default_branch=main` at observation.
- Ruleset `GET /repos/barsam54/PHANTOM/rulesets/27867625`:
  `PHANTOM-MAIN-PROTECTION`, `enforcement=active`, targets
  `~DEFAULT_BRANCH` (main).
- Rules: `deletion`, `non_fast_forward`, `pull_request`,
  `required_status_checks`.
- Required GitHub Actions contexts:
  `Validate repository layout and explain violations` and `build-test`;
  both have GitHub Actions integration ID `15368`.
- `strict_required_status_checks_policy=true`;
  `do_not_enforce_on_create=false`.
- `bypass_actors=[]`; `current_user_can_bypass=never`.

These returned values confirm configured active rules, but a controlled
negative merge/push experiment has **not** been performed, and this
document must not imply that one has.

Official GitHub documentation:
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets

## Follow-up acceptance proof

Use a disposable non-protected feature branch and a separately authorized
negative test that attempts to merge a change with a known failing required
check into main, expecting rejection. Do not force a push, merge PR #1,
alter ruleset settings, or publish a release merely to obtain this proof.
GOV-P0 stays **OPEN**.
