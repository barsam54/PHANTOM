# PHANTOM | Controlled abrupt termination and corrupt manifest rejection

Date: 2026-11-22
Source: user-provided Ubuntu host output
Status: HOST PASS for controlled fault-injection read rejection; overall SML-02 OPEN

- Pulled `64641de..75ce527` (main).
- `dotnet build tests/Phantom.MemoryRestartProbe --no-restore`: succeeded in 1.4s.
- Spawned probe in `stage-partial` mode, waited for `PARTIAL_WRITE_READY` in log, sent SIGKILL (`kill -9`), waited for exit, and started separate `verify-partial` process.
- Observed: `CORRUPT_REJECTED`.
- Interpretation: malformed/truncated JSON manifest was not accepted by `ResearchMemoryStore.ReadAsync`.
- Scope limitation: partial file was deliberately staged by probe, **not** produced by killing `ResearchMemoryStore.SaveAsync` during its write. This does not prove atomic publishing, recovery after interrupted SaveAsync, power-loss durability, or durable Microsoft Agent Framework checkpoint restoration.
- Next gate: design and verify atomic manifest publication with failure/duplicate/concurrent-write negative cases.
