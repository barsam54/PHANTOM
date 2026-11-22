using Microsoft.Agents.AI.Workflows;

namespace Phantom.AgentFramework;

public static class FirstWorkflow
{
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
