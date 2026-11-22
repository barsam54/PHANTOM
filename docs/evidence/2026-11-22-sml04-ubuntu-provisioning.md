# SML-04 Ubuntu provisioning and regression evidence

Date: 2026-11-22
Source: user-provided Ubuntu terminal output; not independently executed by GitHub connector.
Gate: PARTIAL / OPEN.

## Verified observations

- Repository fast-forward updated from `c109477` to `6da6d37`.
- Ubuntu .NET SDK: `10.0.115`; test runner .NET runtime: `10.0.15`; MSTest `4.0.1`.
- `dotnet run --project tests/Phantom.Infrastructure.Tests/Phantom.Infrastructure.Tests.csproj`: **58 succeeded / 0 failed / 0 skipped**, duration **473 ms**, after the pull to `6da6d37`.
- Linux accounts created and independently verified:
  - `phantom-security`: UID **997**, GID **973**.
  - `phantom-worker`: UID **994**, GID **972**.
- `stat` confirmed:
  - `/var/lib/phantom-security`: `phantom-security:phantom-security 700`.
  - `/var/lib/phantom-security/memory`: `phantom-security:phantom-security 700`.
  - `/var/lib/phantom-security/keys`: `phantom-security:phantom-security 700`.
  - `/run/phantom-security`: `phantom-security:phantom-worker 710`.

## Additional live Ubuntu evidence (user-reported, 2026-11-22)

- Private signing key created at `/var/lib/phantom-security/keys/signing.key`: `phantom-security:phantom-security`, mode `0600`, **32 bytes**.
- `dotnet publish src/Phantom.ResearchSecurityHost/Phantom.ResearchSecurityHost.csproj -c Release -o /tmp/phantom-security-publish`: **Build succeeded** in 7.4 s.
- Published host deployed to `/opt/phantom-security`; host DLL confirmed `root:root 644` after correcting initial ownership.
- Trusted host launched as `phantom-security` with effective group `phantom-worker`, experiment `sml04-test`, worker UID **994**, maximum cutoff `2026-12-01T00:00:00.0000000+00:00`. User observed `Research security host listening.`
- Socket `/run/phantom-security/research.sock` confirmed `phantom-security:phantom-worker 660`.
- Cross-UID negative checks: `phantom-worker` cannot read signing key (**PASS**) and cannot traverse private memory (**PASS**).
- Worker connected to Unix socket. Requests using cutoff `2026-12-01` returned `{"error":"denied"}` because the five-minute grant expiry would precede the requested future cutoff. This is **not** evidence of unauthorized-peer rejection.
- Corrected authorized worker request used cutoff one minute before current UTC; server returned a nonempty `{"grant":"..."}` (**PASS**, live positive grant issuance). The secret grant token is intentionally omitted from this evidence.
- Observations are based on user-provided terminal output, not direct execution by the connector.

## Not yet verified

- No admitted memory record read through trusted socket.
- Negative key-read and memory-traversal checks as `phantom-worker` PASS; outsider socket denial and wrong-experiment rejection still PENDING.
- No live key replacement/restart and old-grant rejection.
- Full `scripts/verify-sml04-linux.sh` execution remains PENDING.
- Source changes after `6da6d37` have not been regression-tested on Ubuntu.

Do not infer deployment PASS from filesystem provisioning or unit tests. SML-04 stays OPEN until the operational gate and rotation checks are observed.

## End-to-end operational verification (2026-11-22)

Source: user-provided Ubuntu terminal output.
Execution baseline: commit 6da6d37; documentation subsequently synchronized to a158e72.

- PASS: trusted host restarted after atomic signing-key replacement.
- PASS: outsider `mohsen` denied Unix socket connection.
- PASS: authorized `phantom-worker` received a signed grant.
- PASS: authorized worker read admitted `sml04-test` memory through trusted socket.
- PASS: wrong experiment scope denied.
- PASS: worker denied direct signing-key access and private-memory traversal.
- PASS: socket ownership, group membership and permissions verified.
- PASS: old grant rejected after signing-key replacement.
- PASS: consolidated `scripts/verify-sml04-linux.sh` execution.
- PASS: consolidated command completed with `SML-04 END-TO-END: PASS`.

Limitation: the old grant had a five-minute lifetime. Rejection after rotation
was observed, but the test did not independently establish that the grant
remained unexpired. Rotation-specific rejection therefore remains to be
verified with an unexpired old-key grant.

Gate: operational checks PASS; final SML-04 closure PENDING
rotation-specific proof and evidence commit.

## Final key-rotation evidence

- Grant issued: 2026-11-22T10:34:43.054646Z
- Signing key rotated: 2026-11-22T10:37:22.646912Z
- Grant expired: 2026-11-22T10:40:43.056107Z
- PASS: grant was valid when signing key rotated.
- PASS: old grant signature rejected under rotated key.
- PASS: Linux end-to-end operational verification.
- No secret key or signed grant recorded.
