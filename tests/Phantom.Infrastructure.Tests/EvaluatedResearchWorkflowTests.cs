using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class EvaluatedResearchWorkflowTests
{
    [TestMethod]
    public async Task RealEvaluatedWorkflowPublishesEvidenceAndDurableMemory()
    {
        string root = Path.Combine(Path.GetTempPath(), "phantom-evaluated-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("evaluated-exp-1", "git:integration",
                "phantom", "mode=deterministic");
            DateTimeOffset observation = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
            DateTimeOffset cutoff = observation.AddDays(1);
            string evidence = Path.Combine(root, "evidence");
            string memory = Path.Combine(root, "memory");

            ExperimentResult result = await EvaluatedResearchWorkflow.RunAndRememberAsync(
                request, "MOTNAHP", evidence, memory, observation, cutoff);
            Assert.IsTrue(result.Passed);
            Assert.IsTrue(File.Exists(result.EvidenceLocation));

            ResearchMemoryCandidate restored = await new ResearchMemoryStore(memory)
                .ReadForAuthorizedExperimentAsync(request.ExperimentId, request.ExperimentId, cutoff);
            Assert.AreEqual(request.ExperimentId, restored.ExperimentId);
            Assert.AreEqual(new Uri(result.EvidenceLocation).AbsoluteUri, restored.EvidenceLocation);

            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                new ResearchMemoryStore(memory).ReadForAuthorizedExperimentAsync(
                    request.ExperimentId, "other-experiment", cutoff));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task FailedEvaluationRetainsEvidenceButDoesNotEnterMemory()
    {
        string root = Path.Combine(Path.GetTempPath(), "phantom-evaluated-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("evaluated-fail-1", "git:integration",
                "phantom", "mode=deterministic");
            DateTimeOffset observation = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
            string memory = Path.Combine(root, "memory");
            ExperimentResult result = await EvaluatedResearchWorkflow.RunAndRememberAsync(
                request, "NOT-THE-OUTPUT", Path.Combine(root, "evidence"),
                memory, observation, observation.AddDays(1));
            Assert.IsFalse(result.Passed);
            Assert.IsTrue(File.Exists(result.EvidenceLocation));
            Assert.IsFalse(File.Exists(Path.Combine(memory, request.ExperimentId + ".json")));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }
}
