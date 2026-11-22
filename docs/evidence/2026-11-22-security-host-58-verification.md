# SML-04 security regression: Ubuntu host

Date: 2026-11-22
Source: user-provided terminal output.
- Trusted host build PASS, 2.2s.
- Infrastructure tests 58/58 PASS, failed 0, skipped 0, duration 2.865s.
- Verified through commit `c109477`.
- New non-destructive cross-UID verification script `scripts/verify-sml04-linux.sh` is PENDING execution against an actual provisioned service and distinct host/worker accounts.
- Operational key rotation across process restarts is also PENDING.
- SML-04 OPEN; no release.
