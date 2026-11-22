using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;

namespace Phantom.AgentFramework;

public static class FirstWorkflow
{
    /// <summary>Executes the Agent Framework workflow and records its evaluated output.</summary>
    public static async Task<ExperimentResult> RunWithEvidenceAsync(
        ExperimentRequest request,
        string expectedOutput,
        string evidenceDirectory,
        CancellationToken cancellationToken = default)
    {
        ExperimentContract.Validate(request);
        ArgumentNullException.ThrowIfNull(expectedOutput);
        cancellationToken.ThrowIfCancellationRequested();

        string actual = await RunAsync(request.InputSpecification);
        var evaluator = new LocalEvaluator(EvalChecks.ContainsExpected(true));
        var item = new EvalItem(request.InputSpecification, actual)
        {
            ExpectedOutput = expectedOutput
        };
        AgentEvaluationResults evaluation = await evaluator.EvaluateAsync(
            new[] { item }, "phantom-workflow-evaluation", cancellationToken);

        // ContainsExpected alone allows extra output; exact matching is also required.
        bool exactMatch = string.Equals(actual, expectedOutput, StringComparison.Ordinal);
        bool passed = evaluation.AllPassed && evaluation.Total == 1 &&
            evaluation.Passed == 1 && evaluation.Failed == 0 && exactMatch;
        string testResult = $"Agent Framework LocalEvaluator: " +
            $"total={evaluation.Total}; passed={evaluation.Passed}; " +
            $"failed={evaluation.Failed}; allPassed={evaluation.AllPassed}; " +
            $"exactMatch={exactMatch}; evaluator=ContainsExpected(caseSensitive=true).";

        // Stable across independent runs and evidence directories; binds inputs, code version,
        // configuration, actual output, expected output, and evaluation verdict.
        byte[] canonical = JsonSerializer.SerializeToUtf8Bytes(new
        {
            request.CodeVersion,
            request.InputSpecification,
            request.ExecutionConfiguration,
            ActualOutput = actual,
            ExpectedOutput = expectedOutput,
            evaluation.Total,
            evaluation.Passed,
            evaluation.Failed,
            evaluation.AllPassed,
            ExactMatch = exactMatch
        });
        string fingerprint = Convert.ToHexString(SHA256.HashData(canonical));
        var details = new WorkflowEvaluationEvidence(
            "Microsoft.Agents.AI.LocalEvaluator/ContainsExpected(caseSensitive=true)",
            typeof(LocalEvaluator).Assembly.GetName().Version?.ToString() ?? "unknown",
            actual, expectedOutput, evaluation.Total, evaluation.Passed,
            evaluation.Failed, evaluation.AllPassed, exactMatch, fingerprint);

        return await ExperimentEvidenceStore.SaveAsync(
            request, testResult, passed, evidenceDirectory, cancellationToken, details);
    }

    public static async Task<string> RunAsync(string input)
    {
        ArgumentNullException.ThrowIfNull(input);

        var uppercase = ((Func<string, string>)(value => value.ToUpperInvariant()))
            .BindAsExecutor("UppercaseExecutor");
        var reverse = ((Func<string, string>)(value =>
            string.Concat(value.Reverse()))).BindAsExecutor("ReverseExecutor");

        var builder = new WorkflowBuilder(uppercase);
        builder.AddEdge(uppercase, reverse).WithOutputFrom(reverse);

        await using Run run = await InProcessExecution.RunAsync(builder.Build(), input);

        foreach (WorkflowEvent evt in run.NewEvents)
        {
            if (evt is ExecutorCompletedEvent completed &&
                completed.ExecutorId == "ReverseExecutor" &&
                completed.Data is string output)
            {
                return output;
            }
        }

        throw new InvalidOperationException("Workflow completed without expected output.");
    }
}
