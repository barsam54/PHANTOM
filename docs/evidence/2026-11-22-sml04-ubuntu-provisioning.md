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

## Not yet verified

- No evidence of a 32-byte key provisioned with correct ownership and permissions.
- No trusted host process startup, Unix socket creation, or worker socket connection test.
- No admitted memory record read through trusted socket.
- No negative access check as `phantom-worker` or an outsider UID.
- No live key replacement/restart and old-grant rejection.
- Source changes after `6da6d37` have not been regression-tested on Ubuntu.

Do not infer deployment PASS from filesystem provisioning or unit tests. SML-04 stays OPEN until the operational gate and rotation checks are observed.
