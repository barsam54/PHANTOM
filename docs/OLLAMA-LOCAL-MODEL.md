# PHANTOM | Optional local Ollama model (qwen3:4b)

Status: **PROFILE VERSIONED; LOCAL RUNTIME / INFERENCE NOT VERIFIED BY GITHUB CI**.

## Why this is recorded
The machine `mohsen-nexora` reported successful execution of `ollama pull qwen3:4b` (user-provided terminal result). The downloaded model is **already on the host**. Git contains only a small optional configuration, bootstrap checks and documentation; **not the 2.5 GB model, Ollama executable or runtime cache**.

Versioned profile: `infra/local-models/ollama-qwen3-4b.json`. This model may later be evaluated as an **optional** local development coding-worker candidate. It has no approval to modify code, certify its own work, use research SML evidence, bypass governance, or replace Microsoft Agent Framework orchestration.

## On the host (not in GitHub Actions)
- `ollama list` to confirm the installed tag.
- `python3 scripts/check_local_ollama.py` to validate the repository profile **without making network requests**.
- `python3 scripts/check_local_ollama.py --check-local` to query the loopback-only `GET /api/tags` endpoint and check the exact model name. This does not run inference.
- If local Ollama service is unavailable, use the normal host service management. Do not expose it to the public network or configure a remote endpoint.

Only after an explicit separate authorization should a model-backed worker be integrated, with fixed permissions, input/output minimization, tool restrictions, deterministic negative tests, impact comparison and rollback. The local model may be offline, slow, unavailable, or inaccurate. Neither the download success nor a model-list response proves useful output.

## Official references
- Ollama local API base `http://localhost:11434/api`: https://docs.ollama.com/api/introduction
- List locally available model tags `GET /api/tags`: https://docs.ollama.com/api/tags
- Chat API `POST /api/chat`, optional future use only: https://docs.ollama.com/api/chat
- `qwen3:4b` registry entry: https://ollama.com/library/qwen3:4b

## Microsoft-supported C# agent integration (proposal only)
The optional local worker uses Microsoft's official `OllamaApiClient(...).AsAIAgent(...)` pattern with `OllamaSharp` 5.5.2 and pinned `Microsoft.Agents.AI` 1.28.0. It has **no tools**, shell privileges, repo-write permissions, merge authority or acceptance credentials. Its output must be reviewed as untrusted suggestions, not executed instructions.

The optional CLI is at `src/Phantom.LocalGovernanceCli/`. Run from a PHANTOM checkout:
- Offline configuration check (safe in CI): `dotnet run --project src/Phantom.LocalGovernanceCli -- --check-profile`
- Opt-in localhost model invocation: `printf 'Describe an observed code problem, without secrets' | dotnet run --project src/Phantom.LocalGovernanceCli -- --propose`

The second command only works on a host running Ollama with `qwen3:4b`. It produces a textual, unverified proposal and **does not change code or run a ten-stage phase**. Local inference has not been verified by CI. The repository's official-source decision record is `docs/architecture/SOURCE-FIRST-DECISION.json`.

Microsoft vendor reference: https://learn.microsoft.com/en-us/agent-framework/agents/providers/ollama

## Acceptance limits
- Versioned profile and CI offline tests: checked by repo policy.
- Host model-present check: **NOT PERFORMED** in this PR.
- Local inference quality and integration with Microsoft Agent Framework: **NOT IMPLEMENTED**.
- `GOV-P0`: remains **OPEN**.
