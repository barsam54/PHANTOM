# PHANTOM | Separate-process research memory readback

Date: 2026-11-22
Source: user-provided Ubuntu host output
Status: HOST PASS for clean separate-process memory readback; SML-02 and overall baseline OPEN

- Git fast-forward: `f3912de..64641de`.
- Host created a unique external directory with `mktemp -d`.
- Executed `dotnet run --project tests/Phantom.MemoryRestartProbe -- write "$TEST_DIR"`.
- Observed: `WRITE_PASS`.
- Executed a separate `dotnet run --project tests/Phantom.MemoryRestartProbe -- read "$TEST_DIR"`.
- Observed: `RESTART_READ_PASS`.
- Scope: real Microsoft Agent Framework deterministic workflow output persisted to evidence and immutable local memory manifest; second process reopened and verified it.
- Not tested: forced process termination, incomplete-write recovery, OS/power loss, Agent Framework durable checkpoint persistence/resume, authenticated authorization.
- No full SML stage closure.
