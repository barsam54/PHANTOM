using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class GovernanceLocalProposalAgentTests
{
    [TestMethod]
    public void ReadsVersionedLocalProfileAndConstructsMicrosoftAgentWithoutInference()
    {
        string root = FindRepositoryRoot();
        var settings = GovernanceLocalProposalAgent.ReadConfiguration(
            Path.Combine(root, "infra/local-models/ollama-qwen3-4b.json"));
        Assert.AreEqual("qwen3:4b", settings.Model);
        Assert.IsFalse(settings.EnabledByDefault);
        Assert.IsFalse(settings.ModelArtifactInGit);
        Assert.IsNotNull(GovernanceLocalProposalAgent.Create(settings));
    }

    [TestMethod]
    public void RejectsRemoteEndpointAndCredentials()
    {
        var invalid = new GovernanceLocalProposalAgent.Configuration(
            "ollama", "qwen3:4b", "http://203.0.113.10:11434/", false, false);
        Assert.ThrowsExactly<InvalidOperationException>(() =>
            GovernanceLocalProposalAgent.Validate(invalid));
        Assert.ThrowsExactly<InvalidOperationException>(() =>
            GovernanceLocalProposalAgent.Validate(invalid with
            { ApiBase = "http://user:pass@127.0.0.1:11434/" }));
    }

    [TestMethod]
    public void RejectsEnabledByDefaultOrUnapprovedModel()
    {
        var original = new GovernanceLocalProposalAgent.Configuration(
            "ollama", "qwen3:4b", "http://127.0.0.1:11434", false, false);
        Assert.ThrowsExactly<InvalidOperationException>(() =>
            GovernanceLocalProposalAgent.Validate(original with { EnabledByDefault = true }));
        Assert.ThrowsExactly<InvalidOperationException>(() =>
            GovernanceLocalProposalAgent.Validate(original with { Model = "other:7b" }));
    }

    [TestMethod]
    public async Task DoesNotConnectToLocalHostWhenPromptIsInvalid()
    {
        var settings = new GovernanceLocalProposalAgent.Configuration(
            "ollama", "qwen3:4b", "http://127.0.0.1:11434", false, false);
        await Assert.ThrowsExactlyAsync<ArgumentException>(() =>
            GovernanceLocalProposalAgent.ProposeAsync(settings, " "));
        await Assert.ThrowsExactlyAsync<ArgumentOutOfRangeException>(() =>
            GovernanceLocalProposalAgent.ProposeAsync(settings, new string('x', 8001)));
    }

    private static string FindRepositoryRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName,
                "infra/local-models/ollama-qwen3-4b.json")))
                return current.FullName;
            current = current.Parent;
        }
        throw new InvalidOperationException("Cannot locate PHANTOM local-model profile.");
    }
}
