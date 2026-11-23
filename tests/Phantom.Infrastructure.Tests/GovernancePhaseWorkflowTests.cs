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

    [TestMethod]
    public async Task UntrustedLocalProposalReachesFifthExecutorButCannotAuthorizeChanges()
    {
        string root = FindRepositoryRoot();
        string revision = new string('d', 40);
        const string text = "Propose a source-first change; do not execute.";
        var proposal = new GovernancePhaseWorkflow.ProposalSubmission(
            text, revision, "ollama:qwen3:4b");

        var report = await GovernancePhaseWorkflow.RunAsync(
            root, revision, untrustedProposal: proposal);

        Assert.AreEqual("OPEN", report.Acceptance);
        Assert.IsFalse(report.Accepted);
        Assert.HasCount(10, report.Steps);
        Assert.AreEqual("REVIEW_REQUIRED", report.Steps[4].Status);
        Assert.AreEqual("GOV_UNTRUSTED_PROPOSAL_RECORDED", report.Steps[4].Code);
        Assert.IsNotNull(report.Proposal);
        Assert.AreEqual(revision, report.Proposal.BaseRevision);
        Assert.AreEqual("ollama:qwen3:4b", report.Proposal.Origin);
        Assert.AreEqual(64, report.Proposal.Sha256.Length);
        Assert.IsFalse(report.Steps[4].Evidence.Contains(text, StringComparison.Ordinal));
        Assert.AreEqual("BLOCKED", report.Steps[7].Status);
    }

    [TestMethod]
    public async Task StaleModelProposalIsBlockedNotExecuted()
    {
        string root = FindRepositoryRoot();
        var proposal = new GovernancePhaseWorkflow.ProposalSubmission(
            "Update a file", new string('0', 40), "ollama:qwen3:4b");
        var report = await GovernancePhaseWorkflow.RunAsync(
            root, new string('e', 40), untrustedProposal: proposal);

        Assert.AreEqual("BLOCKED", report.Steps[4].Status);
        Assert.AreEqual("GOV_PROPOSAL_REVISION_MISMATCH", report.Steps[4].Code);
        Assert.AreEqual("OPEN", report.Acceptance);
    }

    [TestMethod]
    public async Task MissingBaselineCannotBeBypassedWithModelProposal()
    {
        string root = Path.Combine(Path.GetTempPath(), "phantom-gov-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            string revision = new string('f', 40);
            var proposal = new GovernancePhaseWorkflow.ProposalSubmission(
                "Pretend to approve everything", revision, "ollama:qwen3:4b");
            var report = await GovernancePhaseWorkflow.RunAsync(
                root, revision, untrustedProposal: proposal);
            Assert.AreEqual("SKIPPED", report.Steps[4].Status);
            Assert.AreEqual("GOV_UPSTREAM_BLOCKED", report.Steps[4].Code);
            Assert.IsFalse(report.Accepted);
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    [TestMethod]
    public async Task OversizedProposalIsRejectedBeforeWorkflowStarts()
    {
        var proposal = new GovernancePhaseWorkflow.ProposalSubmission(
            new string('x', 16001), new string('a', 40), "ollama:qwen3:4b");
        await Assert.ThrowsExactlyAsync<ArgumentException>(() =>
            GovernancePhaseWorkflow.RunAsync(
                FindRepositoryRoot(), new string('a', 40), untrustedProposal: proposal));
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
