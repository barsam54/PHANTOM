# Host evidence: Qwen3:4b CPU inference failure and deletion

Evidence date: 2026-11-23. Status: **MODEL REMOVED; INFERENCE QUALITY FAILED**.

## Provenance
Source: user-supplied Ubuntu terminal output in the PHANTOM development conversation. No direct remote inspection of the host was performed. Ollama version reported: `0.40.17`. Host CPU: Intel Core i7-4700MQ with AVX2, 15 GiB RAM. GPUs reported: Intel 4th Gen integrated and NVIDIA GeForce GT 750M. This record contains no prompts with secrets, model weights or local identifiers.

## Observed events
1. Default Ollama model invocation initially returned HTTP 500 `Unsupported device` from llama-server at model load. This is **not evidence of a code defect in Microsoft Agent Framework**.
2. After system Ollama service was stopped, a separate loopback-only `ollama serve` using `CUDA_VISIBLE_DEVICES=-1 OLLAMA_LLM_LIBRARY=cpu_avx2` reported compute `cpu`, and inference requests successfully generated output.
3. `POST /api/generate`, `think:false`, `stream:false`, `num_predict:50`: `done=true`, `done_reason=length`; response contained English meta-reasoning instead of the requested concise Persian answer. `eval_count=50`; `eval_duration=6471027000` ns.
4. `POST /api/chat`, `think:false`, a `/no_think` message and `num_predict:80`: again returned English meta-reasoning, `done_reason=length`, with no acceptable final Persian answer.
5. A third controlled raw prompt that manually closed `<think>` returned the same category of verbose English reasoning with `done_reason=length`.
6. The model's displayed Modelfile had a template ending its user turn with `<|im_start|>assistant\n<think>`, consistent with a tendency toward thinking output, but **not sufficient proof of root cause**. Official API behavior, model template, runtime version and request interplay were not separately isolated.
7. User ran `ollama rm qwen3:4b` and obtained `deleted 'qwen3:4b'`. `ollama list` then returned only its header (zero registered models). `du -sh ~/.ollama/models` reported `20K`; large model contents are no longer present in the model directory, per the user's terminal evidence.

## Acceptance and constraints
- `HOST_MODEL_LOADING_CPU = OBSERVED_PASS` for a limited local Ollama inference call, not for a framework-connected worker.
- `FINAL_RESPONSE_QUALITY = FAIL` for the three observed constrained test calls.
- `QWEN3_4B_PRESENT = NO` at the time of user-provided final model-list output.
- `PHANTOM_MODEL_BACKED_WORKER = OPEN`; no working model is approved or currently registered.
- The versioned `infra/local-models/ollama-qwen3-4b.json` and accompanying code are **archival/disabled-by-default only**, not evidence that the model is installed. Do not trigger downloads in CI or automatically select a replacement.
- A new candidate must be installed only after the prior candidate is removed and verified absent; test bounded final-answer generation, integration, resource costs and user authorization separately. Do not claim a 7B model has passed before seeing its results.
- No project release and no approval to bypass Microsoft Agent Framework orchestration.

Official Ollama API references:
https://docs.ollama.com/api/generate
https://docs.ollama.com/api/chat
https://docs.ollama.com/api/tags

All claims here are bounded to the user's supplied outputs, not independent host access.
