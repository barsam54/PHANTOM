namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class InfrastructureConfigurationTests
{
    [TestMethod]
    public void TestProjectMustUseMicrosoftTestingPlatform()
    {
        var project = Path.Combine(
            AppContext.BaseDirectory,
            "..", "..", "..",
            "Phantom.Infrastructure.Tests.csproj");

        var content = File.ReadAllText(Path.GetFullPath(project));

        StringAssert.Contains(
            content,
            "<EnableMSTestRunner>true</EnableMSTestRunner>");
    }
}
