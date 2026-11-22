using Microsoft.Agents.AI.Workflows;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class WorkflowCheckpointTests
{
    [TestMethod]
    public async Task StreamingWorkflowCapturesCheckpointsAndRestoresOutput()
    {
        var uppercase = ((Func<string, string>)(value => value.ToUpperInvariant()))
            .BindAsExecutor("CheckpointUppercaseExecutor");
        var reverse = ((Func<string, string>)(value => string.Concat(value.Reverse())))
            .BindAsExecutor("CheckpointReverseExecutor");

        var builder = new WorkflowBuilder(uppercase);
        builder.AddEdge(uppercase, reverse).WithOutputFrom(reverse);

        CheckpointManager checkpointManager = CheckpointManager.CreateInMemory();
        await using StreamingRun run = await InProcessExecution.RunStreamingAsync(
            builder.Build(), "PHANTOM", checkpointManager);

        string? initialOutput = null;
        await foreach (WorkflowEvent evt in run.WatchStreamAsync())
        {
            if (evt is WorkflowOutputEvent output && output.Data is string value)
                initialOutput = value;
        }

        Assert.AreEqual("MOTNAHP", initialOutput);
        Assert.IsTrue(run.Checkpoints.Count >= 2,
            "Expected a checkpoint after each of the two executor supersteps.");

        // Restore the checkpoint after the first executor. The second executor
        // should then produce the same result without re-entering the first.
        CheckpointInfo checkpoint = run.Checkpoints[0];
        await run.RestoreCheckpointAsync(checkpoint);

        string? restoredOutput = null;
        await foreach (WorkflowEvent evt in run.WatchStreamAsync())
        {
            if (evt is WorkflowOutputEvent output && output.Data is string value)
                restoredOutput = value;
        }

        Assert.AreEqual(initialOutput, restoredOutput);
    }
}
