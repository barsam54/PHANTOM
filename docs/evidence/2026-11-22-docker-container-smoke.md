# PHANTOM | Docker Container Smoke Checkpoint

Date: 2026-11-22
Evidence ID: PHANTOM-INFRA-DOCKER-20261122-001
Source: user-reported terminal output (not machine-captured)
Status: PARTIAL — container execution observed; security enforcement and exit code not independently verified.

## Host and engine
- Host: Ubuntu Linux, amd64.
- Docker client: 29.1.3.
- Docker service: active.
- Ordinary user access to /var/run/docker.sock: permission denied.
- Privileged daemon query via sudo: PASS.
- Docker security options reported: apparmor, seccomp (builtin profile), cgroupns.
- Cgroup version: 2; storage driver: overlayfs.
- Local images initially: none.
- Attempted alpine:3.22 pull: FAIL, Docker Hub registry HEAD returned HTTP 403. This is a registry retrieval failure, not evidence of a container runtime failure.

## Official .NET image
- Image: mcr.microsoft.com/dotnet/sdk:10.0-noble.
- Pull result: PASS.
- Reported digest: sha256:bef136a371963aaa46ec97882845ef6f54dec15728bb4b128b1c2a400ffbc9b4.

## Container smoke invocation
```sh
sudo docker run --rm \
  --pull=never \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --memory 512m \
  --cpus 0.5 \
  --pids-limit 64 \
  --user 65534:65534 \
  mcr.microsoft.com/dotnet/sdk:10.0-noble \
  dotnet --info
```

## Observed output
- .NET SDK: 10.0.404 at /usr/share/dotnet/sdk.
- Host runtime: 10.0.15; linux-x64.
- Microsoft.AspNetCore.App: 10.0.15.
- Microsoft.NETCore.App: 10.0.15.
- DOTNET_RUNNING_IN_CONTAINER=true.
- Warning: "The user's home directory could not be determined. Set the 'DOTNET_CLI_HOME' environment variable to specify the directory to use."
- Command returned to the interactive shell; numeric exit code not captured.

## Acceptance boundary
- PASS: image retrieval, container startup, and successful display of dotnet --info.
- CONFIGURED IN INVOCATION, NOT INDEPENDENTLY VERIFIED: no network, read-only root filesystem, all capabilities dropped, no-new-privileges, 512 MiB memory, 0.5 CPU, 64 PIDs, UID/GID 65534.
- OPEN: assert actual restrictions inside the container; capture numeric exit code; validate non-root writable-home strategy for .NET operations; build/test PHANTOM in a container; isolation against untrusted code; automatic evidence recording.
- No claim of safe execution of third-party trading code, cTrader compatibility, or full baseline acceptance.

## Restricted-container enforcement check (2026-11-22)
Evidence ID: PHANTOM-INFRA-DOCKER-20261122-002
Source: user-reported terminal output; numeric exit code captured.
Image: mcr.microsoft.com/dotnet/sdk:10.0-noble (already downloaded).
Invocation flags: --network none, --read-only, --cap-drop ALL, --security-opt no-new-privileges, --memory 512m, --memory-swap 512m, --cpus 0.5, --pids-limit 64, --user 65534:65534.

Observed:
- id: uid=65534(nobody), gid=65534(nogroup), groups=65534(nogroup) — PASS.
- /proc/self/status: CapEff=0000000000000000 — PASS.
- /proc/self/status: NoNewPrivs=1 — PASS.
- /proc/net/route: header only, no routes — PASS for absence of routes; independent connectivity denial not tested.
- /sys/fs/cgroup/memory.max: 536870912 (512 MiB) — PASS.
- /sys/fs/cgroup/cpu.max: 50000 100000 (0.5 CPU quota) — PASS.
- /sys/fs/cgroup/pids.max: 64 — PASS.
- touch /phantom-write-test: failed; read-only root filesystem check PASS.
- DOCKER_EXIT_CODE=0 — PASS.

Acceptance:
- PASS: this specific restricted-container smoke test and observed controls.
- OPEN: execution of untrusted code; explicit network connectivity negative test; non-root writable-home strategy for SDK build/test; per-experiment filesystem mounts and artifact handling; timeout and cancellation; repeatability and automated evidence capture.
- This evidence is based on pasted terminal output, not a cryptographically attested execution trace.
