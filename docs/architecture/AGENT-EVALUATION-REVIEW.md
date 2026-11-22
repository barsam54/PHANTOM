# PHANTOM — Microsoft Agent Framework evaluation assessment
Date: 2026-11-22
Status: LOCAL EVALUATION AND WORKFLOW INTEGRATION VERIFIED; BROADER EVALUATION OPEN

## Baseline mapping
Baseline section 9, gate 3 requires a **real agent or workflow evaluation**. The current uppercase/reverse workflow and expected-output check are deterministic smoke checks, **not** evidence of executing Agent Framework's built-in evaluation API.

## Official Microsoft documentation reviewed
- https://learn.microsoft.com/en-us/agent-framework/agents/evaluation
- https://learn.microsoft.com/en-us/agent-framework/agents/observability
- https://learn.microsoft.com/en-us/agent-framework/workflows/observability
- https://learn.microsoft.com/en-us/agent-framework/overview

## Documented .NET evaluation approach
- Microsoft Agent Framework exposes evaluation on `AIAgent` and `Run` through `EvaluateAsync`, with `AgentEvaluationResults`.
- Evaluators are represented through `IAgentEvaluator`; .NET evaluation integrates with `Microsoft.Extensions.AI.Evaluation`.
- Microsoft Foundry evaluation is supported, but must not be silently assumed configured or available.
- Workflow evaluation can report overall and per-agent results; an ordinary function-only workflow does not establish per-agent evaluation.
- Observability uses OpenTelemetry; tracing is **not** a substitute for evaluation. Sensitive prompt/response capture should stay disabled unless explicitly justified.

## Required next verification before coding
1. Inspect locally restored Microsoft.Agents.AI 1.28.0 APIs, transitive evaluation package availability and documented API signatures. Current online docs may describe a newer version.
2. Choose a real evaluator and deterministic test case that can run with available local dependencies, or document a provider/configuration prerequisite if model-backed evaluation is required.
3. Implement and execute an actual Agent Framework evaluation API call; record evaluator identity/version, inputs, expected criteria, result and evidence location.
4. Assert explicit pass/fail from evaluation results, test failure cases, and avoid treating a successful API call as scientific correctness.
5. Keep workflow orchestration exclusively within Microsoft Agent Framework.

## Acceptance state
- Gate 3: PASS for deterministic local evaluation of real workflow output (user-reported 16/16 passing tests, 2026-11-22); broader agent/model-backed evaluation remains OPEN.
- Gate 4: PARTIAL (JSON persistence and LocalEvaluator integration tests pass; structured evaluation artifact and independent evidence review remain OPEN).
- Gate 5: PARTIAL (deterministic smoke check; scientific reproducibility OPEN).
- Full baseline: OPEN.

## Installed API verification — user terminal evidence (2026-11-22)
- Project: Microsoft.Agents.AI 1.28.0 and Microsoft.Agents.AI.Workflows 1.28.0.
- Transitive: Microsoft.Extensions.AI.Evaluation 10.11.0.
- net10.0 XML API documentation confirms AgentEvaluationExtensions.EvaluateAsync overloads, AgentEvaluationResults, IAgentEvaluator, LocalEvaluator(EvalCheck[]), and EvalChecks including KeywordCheck, NonEmpty and ContainsExpected.
- This verifies package/API availability, **not** successful invocation or behavior.
- Next implementation: use local evaluation API in a minimal real agent test, verify exact method signatures and result semantics by compiling and running MSTest. No new packages should be needed.
- LocalEvaluator positive and negative cases assert Total/Passed/Failed/AllPassed; user-reported test run: 16 passed, 0 failed, 0 skipped, 3.723 seconds.\n- FirstWorkflow.RunWithEvidenceAsync now invokes LocalEvaluator(ContainsExpected(caseSensitive=true)) on actual workflow output, combines the evaluator result with exact output matching, and persists the outcome. User-reported test run: 16 passed, 0 failed, 0 skipped, 3.734 seconds.\n- These are local deterministic evaluations; no external judge model, real trading strategy evaluation, or scientific reproducibility is claimed.
