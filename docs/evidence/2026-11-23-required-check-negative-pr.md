# GOV-P0 | Non-draft PR with failed required check is blocked

Observation date: 2026-11-23. Status: **NEGATIVE RULESET GATE VERIFIED (READBACK)**.

## Method
1. Read `main` commit `6c0247f844986bc0f5c5e8c5b04a0c25d516f9e7` and confirmed protected branch.
2. Created throwaway branch `governance/negative-required-check-probe-20261123` from main, then committed `GOV_PROTECTION_NEGATIVE_PROBE.txt` at repository root. This violates the existing root-layout policy by design.
3. Opened non-draft test PR #2 targeting protected `main` (head `79bb26f0ab563323bb8090fbe425654ef6ce20bf`).
4. GitHub Actions `Repository Policy Guard` run `45097741706`: **failure**. Step `Check tracked files against baseline`: **failure**.
5. With the failed required check and `draft=false`, GitHub REST `GET /repos/barsam54/PHANTOM/pulls/2` reported `mergeable=true`, `mergeable_state=blocked`. The mergeable property describes merge conflict possibility; the server's separate **blocked** state indicates current merge gate denial.
6. Closed PR #2 without merging. `merged=false`; protected `main` unchanged.

## Interpretation
The observed behavior demonstrates that a PR with failed required repository policy is marked **blocked** by GitHub's merge gate on this protected branch. The configured active ruleset #27867625 has no bypass actors and requires `Validate repository layout and explain violations` and `build-test` from GitHub Actions.

This is **not** evidence of an attempted rejected `POST /pulls/2/merge` or a rejected unauthorized direct push, since those destructive operations were deliberately not attempted. It also does not prove semantic vendor source correctness or full governance lifecycle acceptance.

Test PR: https://github.com/barsam54/PHANTOM/pull/2 (closed, unmerged).
Official GitHub documentation:
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

**GOV-P0 remains OPEN**: worker authorization, independently measured change impact and external-side-effect recovery are not accepted.
