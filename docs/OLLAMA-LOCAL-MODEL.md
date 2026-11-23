# PHANTOM | Archived optional local Ollama model profile (qwen3:4b)

Status: **ARCHIVED PROFILE; HOST MODEL REMOVED; NO APPROVED LOCAL INFERENCE MODEL**. GitHub CI does not run host inference.

Host evidence: `docs/evidence/2026-11-23-host-ollama-inference-removal.md` records CPU-only successful token generation, failed final-answer quality, removal of `qwen3:4b` and zero installed models at the observed time. The profile remains disabled and does not imply current installation.

## Why this is recorded
The host previously downloaded `qwen3:4b`, but the user has since removed it. The latest terminal report shows `ollama list` empty and only `20K` remaining under `~/.ollama/models`. **The model is no longer installed.** Git contains only a small optional configuration, bootstrap checks and documentation; **not the 2.5 GB model, Ollama executable or runtime cache**.

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

The second command **cannot currently succeed as configured**, because `qwen3:4b` has been removed. Do not run it or re-download a model implicitly. It only works after explicit authorization, installation, and separate acceptance of a suitable model. It produces a textual, unverified proposal and **does not change code or run a ten-stage phase**. Local inference has not been verified by CI. The repository's official-source decision record is `docs/architecture/SOURCE-FIRST-DECISION.json`.

Microsoft vendor reference: https://learn.microsoft.com/en-us/agent-framework/agents/providers/ollama

## Governance step 5 handoff (read-only)
- Offline CI integration proof: `dotnet run --project src/Phantom.LocalGovernanceCli -- --probe-workflow`. This injects a **synthetic** proposal, not a local Ollama response. The existing Microsoft Agent Framework ten-executor workflow records only its SHA-256, bound Git HEAD and source label. The fifth executor returns `REVIEW_REQUIRED`; acceptance remains `OPEN`.
- Explicit real-model handoff on a clean local checkout: `printf 'Describe a narrow, nonsensitive software issue' | dotnet run --project src/Phantom.LocalGovernanceCli -- --propose-workflow`. This calls local Ollama once and passes the untrusted result to the same workflow. The CLI prints the structured ten-stage report, **not the model text**; use `--propose` to inspect plain unverified text separately.
- The CLI refuses an uncommitted/dirty Git worktree, oversized source input, invalid local endpoint, or missing Ollama runtime. A model proposal against a different revision is rejected. The workflow does not use the model to write files and cannot make an acceptance decision.
- Independent review of official sources, impact, tests, and rollback is still required; a proposal digest is an integrity marker, not authentication or truth.

## Acceptance limits
- Versioned profile and CI offline tests: checked by repo policy.
- User-observed host model availability: **ZERO installed models after removal**; GitHub CI has no direct host access.
- CPU token generation on removed Qwen3 model: **OBSERVED**, but bounded final-response evaluation: **FAIL**.
- Model-backed Microsoft Agent Framework integration acceptance: **OPEN**; no model candidate approved.
- `GOV-P0`: remains **OPEN**.
