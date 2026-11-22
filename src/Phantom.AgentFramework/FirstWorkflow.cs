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
        bool passed = string.Equals(actual, expectedOutput, StringComparison.Ordinal);
        string testResult = passed
            ? "Workflow output matched expected output."
            : "Workflow output did not match expected output.";

        return await ExperimentEvidenceStore.SaveAsync(
            request, testResult, passed, evidenceDirectory, cancellationToken);
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
