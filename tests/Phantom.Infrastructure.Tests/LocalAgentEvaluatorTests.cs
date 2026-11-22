using Microsoft.Agents.AI;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class LocalAgentEvaluatorTests
{
    [TestMethod]
    public async Task EvaluatesPassingResponseWithRealLocalEvaluator()
    {
        var evaluator = new LocalEvaluator(
            EvalChecks.KeywordCheck("PHANTOM"),
            EvalChecks.NonEmpty(1));
        var items = new[] { new EvalItem("Name the project", "PHANTOM") };
        var results = await evaluator.EvaluateAsync(items, "phantom-local-smoke", CancellationToken.None);

        Assert.IsNotNull(results);
        Assert.AreEqual(1, results.Total);
        Assert.AreEqual(1, results.Passed);
        Assert.AreEqual(0, results.Failed);
        Assert.IsTrue(results.AllPassed);
    }

    [TestMethod]
    public async Task EvaluatesFailingResponseWithRealLocalEvaluator()
    {
        var evaluator = new LocalEvaluator(EvalChecks.KeywordCheck("PHANTOM"));
        var items = new[] { new EvalItem("Name the project", "OTHER") };
        var results = await evaluator.EvaluateAsync(items, "phantom-local-smoke", CancellationToken.None);

        Assert.IsNotNull(results);
        Assert.AreEqual(1, results.Total);
        Assert.AreEqual(0, results.Passed);
        Assert.AreEqual(1, results.Failed);
        Assert.IsFalse(results.AllPassed);
    }
}
