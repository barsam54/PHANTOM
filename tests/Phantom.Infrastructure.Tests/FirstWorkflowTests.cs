using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class FirstWorkflowTests
{
    [TestMethod]
    public async Task RunsBothExecutorsAndReturnsExpectedOutput()
    {
        string actual = await FirstWorkflow.RunAsync("Hello, World!");
        Assert.AreEqual("!DLROW ,OLLEH", actual);
    }

    [TestMethod]
    public async Task ProducesSameResultAcrossRepeatedRuns()
    {
        string first = await FirstWorkflow.RunAsync("PHANTOM");
        string second = await FirstWorkflow.RunAsync("PHANTOM");

        Assert.AreEqual("MOTNAHP", first);
        Assert.AreEqual(first, second);
    }

    [TestMethod]
    public async Task RejectsNullInput()
    {
        await Assert.ThrowsExactlyAsync<ArgumentNullException>(
            () => FirstWorkflow.RunAsync(null!));
    }
}
