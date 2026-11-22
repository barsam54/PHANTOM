# SML-04 Linux trusted host deployment contract

Status: NOT DEPLOYED / OPEN.

This is a specification for an administrator, **not** authorization to create users,
change ownership, grant sudo access, or start a service on a user's machine.

## Security identities

- Provision distinct, non-root `phantom-security` and `phantom-worker` accounts.
- Run trusted host as `phantom-security` with effective group equal to the
  worker's dedicated socket-access group. Do not give the worker membership
  in the trusted host's private storage group or access to host credentials.
- Ensure all parent paths are not symlinks. Storage and key directories must
  be owned by the host account and mode `0700`. Signing key: exactly 32 random
  bytes, owner host, mode `0600` (or `0400`).
- Socket directory: owner host, group socket-access, mode `0710`.
  Socket: owner host, group socket-access, mode `0660`.
- Worker must not have traversal rights to storage or key directory. Worker
  cannot run as root or as host UID. Root administrators are outside this
  Unix discretionary-access threat model.

## Startup

Build `src/Phantom.ResearchSecurityHost/Phantom.ResearchSecurityHost.csproj`
and run as the trusted non-root account:

```text
dotnet Phantom.ResearchSecurityHost.dll <socket-directory> <memory-directory> <key-file> <experiment-id> <worker-uid> <maximum-cutoff-utc-O>
```

Host refuses root and same-UID startup; it validates private memory and key
directory modes, socket directory mode and socket path. An administrator must
verify ownership and group mappings separately. The host does not create users
or provision groups.

## Rotation and revocation

Replace the private 32-byte key through a privileged atomic provisioning
procedure and restart the trusted host. The old host must stop accepting
requests before the replacement host starts. Grants signed by the old key
are invalid with the new key; the rotation unit test proves this property.
No live hot-reload or key-ring grace period is supported. No persistent
grant revocation list exists; immediate revocation requires restart and
replacement key. Never store keys in Git, logs, or environment variables.

## Evidence gate

Run `scripts/verify-sml04-linux.sh` only after the administrator has
provisioned and started the service; set the seven required `PHANTOM_*`
environment variables documented in that script. The script checks
actual UID separation, ownership, permissions, worker inability to read key
or traverse memory, and allowed/denied socket grants. It uses `sudo -n`
for checks and never modifies permissions or users.

SML-04 cannot close without captured host output of that script, a positive
read of an admitted memory record under the correct cutoff, a real
restart/key-rotation check, and regression tests. All are currently OPEN.
