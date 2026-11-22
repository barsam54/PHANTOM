using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class WorkflowStateIsolationTests
{
    [TestMethod]
    public async Task ConcurrentWorkflowRunsKeepInputsAndOutputsIsolated()
    {
        const int count = 12;
        string[] inputs = Enumerable.Range(0, count)
            .Select(i => $"RUN-{i:D2}-unique-{Guid.NewGuid():N}")
            .ToArray();

        Task<string>[] runs = inputs.Select(FirstWorkflow.RunAsync).ToArray();
        string[] outputs = await Task.WhenAll(runs);

        Assert.HasCount(count, outputs);
        for (int i = 0; i < count; i++)
        {
            string expected = string.Concat(inputs[i].ToUpperInvariant().Reverse());
            Assert.AreEqual(expected, outputs[i], $"Run {i} received another run's output.");
        }

        Assert.AreEqual(count, outputs.Distinct(StringComparer.Ordinal).Count());
    }

    [TestMethod]
    public async Task SubsequentRunDoesNotInheritPreviousRunInput()
    {
        string first = await FirstWorkflow.RunAsync("FIRST-PRIVATE-STATE");
        string second = await FirstWorkflow.RunAsync("SECOND-ISOLATED");

        Assert.AreEqual("ETATS-ETAVIRP-TSRIF", first);
        Assert.AreEqual("DETALOSI-DNOCES", second);
        Assert.IsFalse(second.Contains("FIRST", StringComparison.Ordinal));
    }
}
