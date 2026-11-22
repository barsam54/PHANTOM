using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class GovernancePhaseWorkflowTests
{
    [TestMethod]
    public async Task RunsTenOrderedFrameworkExecutorsWithoutFalseAcceptance()
    {
        string repository = FindRepositoryRoot();
        var report = await GovernancePhaseWorkflow.RunAsync(repository, new string('a', 40));

        Assert.AreEqual("GOV-P0", report.Gate);
        Assert.AreEqual("OPEN", report.Acceptance);
        Assert.IsFalse(report.Accepted);
        Assert.HasCount(10, report.Steps);
        CollectionAssert.AreEqual(GovernancePhaseWorkflow.OrderedStages,
            report.Steps.Select(x => x.Step).ToArray());
        Assert.AreEqual("CHECK_OK", report.Steps[0].Status);
        Assert.AreEqual("NOT_IMPLEMENTED", report.Steps[4].Status);
        Assert.AreEqual("BLOCKED", report.Steps[7].Status);
        Assert.AreEqual("NOT_IMPLEMENTED", report.Steps[9].Status);
        foreach (var decision in report.Steps)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(decision.Code));
            Assert.IsFalse(string.IsNullOrWhiteSpace(decision.Reason));
            Assert.IsFalse(string.IsNullOrWhiteSpace(decision.Action));
            Assert.IsFalse(string.IsNullOrWhiteSpace(decision.Evidence));
            Assert.IsFalse(string.IsNullOrWhiteSpace(decision.Resume));
        }
    }

    [TestMethod]
    public async Task MissingBaselineIsReportedButCannotSelfCertify()
    {
        string root = Path.Combine(Path.GetTempPath(), "phantom-gov-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var report = await GovernancePhaseWorkflow.RunAsync(root, new string('b', 40));
            Assert.AreEqual("BLOCKED", report.Steps[0].Status);
            Assert.AreEqual("BLOCKED", report.Steps[1].Status);
            Assert.AreEqual("SKIPPED", report.Steps[4].Status);
            Assert.AreEqual("GOV_UPSTREAM_BLOCKED", report.Steps[4].Code);
            Assert.AreEqual("OPEN", report.Acceptance);
            Assert.IsFalse(report.Accepted);
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    [TestMethod]
    public async Task RejectsInvalidRepositoryRootBeforeWorkflow()
    {
        await Assert.ThrowsExactlyAsync<ArgumentException>(
            () => GovernancePhaseWorkflow.RunAsync("relative/path", new string('c', 40)));
    }

    private static string FindRepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName,
                    "docs/architecture/GOVERNANCE-CONTRACT.json")) &&
                File.Exists(Path.Combine(directory.FullName, "global.json")))
                return directory.FullName;
            directory = directory.Parent;
        }
        throw new InvalidOperationException("Cannot locate PHANTOM repository root for integration test.");
    }
}
