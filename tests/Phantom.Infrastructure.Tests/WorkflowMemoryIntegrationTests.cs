using System.Security.Cryptography;
using System.Text;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class WorkflowMemoryIntegrationTests
{
    [TestMethod]
    public async Task RealAgentFrameworkWorkflowOutputPersistsAndRestoresWithScopedMemory()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-integration-{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(root);
            string actual = await FirstWorkflow.RunAsync("phantom");
            Assert.AreEqual("MOTNAHP", actual);

            string evidencePath = Path.Combine(root, "workflow-output.txt");
            byte[] bytes = Encoding.UTF8.GetBytes(actual);
            await File.WriteAllBytesAsync(evidencePath, bytes);

            var observation = new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
            var cutoff = observation.AddDays(1);
            var candidate = new ResearchMemoryCandidate(
                "workflow-exp-1", "integration-test-v1",
                new Uri(evidencePath).AbsoluteUri,
                Convert.ToHexString(SHA256.HashData(bytes)),
                observation, cutoff, "train", true);
            string memoryRoot = Path.Combine(root, "memory");
            await new ResearchMemoryStore(memoryRoot).SaveAsync(candidate);

            var reopened = new ResearchMemoryStore(memoryRoot);
            ResearchMemoryCandidate restored =
                await reopened.ReadForAuthorizedExperimentAsync(
                    "workflow-exp-1", "workflow-exp-1", cutoff);
            Assert.AreEqual(candidate, restored);
            Assert.AreEqual("MOTNAHP", await File.ReadAllTextAsync(new Uri(restored.EvidenceLocation).LocalPath));

            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reopened.ReadForAuthorizedExperimentAsync(
                    "workflow-exp-1", "unrelated-exp", cutoff));

            await File.WriteAllTextAsync(evidencePath, "tampered");
            await Assert.ThrowsExactlyAsync<InvalidDataException>(() =>
                reopened.ReadForAuthorizedExperimentAsync(
                    "workflow-exp-1", "workflow-exp-1", cutoff));
        }
        finally
        {
            if (Directory.Exists(root))
                Directory.Delete(root, recursive: true);
        }
    }
}
