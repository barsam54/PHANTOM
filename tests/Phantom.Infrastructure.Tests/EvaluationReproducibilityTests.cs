using System.Text.Json;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class EvaluationReproducibilityTests
{
    [TestMethod]
    public async Task IndependentRunsPersistIdenticalEvaluationEvidence()
    {
        string aDir = Path.Combine(Path.GetTempPath(), "phantom-repro-" + Guid.NewGuid().ToString("N"));
        string bDir = Path.Combine(Path.GetTempPath(), "phantom-repro-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("REPRO-A", "git:fixed", "PHANTOM", "smoke=uppercase-reverse");
            ExperimentResult a = await FirstWorkflow.RunWithEvidenceAsync(request, "MOTNAHP", aDir);
            ExperimentResult b = await FirstWorkflow.RunWithEvidenceAsync(
                request with { ExperimentId = "REPRO-B" }, "MOTNAHP", bDir);
            Assert.IsTrue(a.Passed);
            Assert.IsTrue(b.Passed);
            Assert.IsNotNull(a.Evaluation);
            Assert.IsNotNull(b.Evaluation);
            Assert.AreEqual(a.Evaluation, b.Evaluation);
            Assert.AreEqual(64, a.Evaluation.ReproductionFingerprint.Length);
            Assert.AreNotEqual(a.EvidenceLocation, b.EvidenceLocation);
            ExperimentResult? persisted = JsonSerializer.Deserialize<ExperimentResult>(
                await File.ReadAllTextAsync(a.EvidenceLocation));
            Assert.IsNotNull(persisted);
            Assert.AreEqual(a, persisted);
            Assert.AreEqual(1, persisted.Evaluation?.Passed);
            Assert.AreEqual(0, persisted.Evaluation?.Failed);
            Assert.IsTrue(persisted.Evaluation!.AllPassed);
        }
        finally
        {
            if (Directory.Exists(aDir)) Directory.Delete(aDir, true);
            if (Directory.Exists(bDir)) Directory.Delete(bDir, true);
        }
    }

    [TestMethod]
    public async Task FailedEvaluationIsPersistedAndChangesFingerprint()
    {
        string aDir = Path.Combine(Path.GetTempPath(), "phantom-repro-" + Guid.NewGuid().ToString("N"));
        string bDir = Path.Combine(Path.GetTempPath(), "phantom-repro-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("REPRO-C", "git:fixed", "PHANTOM", "smoke=uppercase-reverse");
            ExperimentResult a = await FirstWorkflow.RunWithEvidenceAsync(request, "MOTNAHP", aDir);
            ExperimentResult b = await FirstWorkflow.RunWithEvidenceAsync(
                request with { ExperimentId = "REPRO-D" }, "WRONG", bDir);
            Assert.IsTrue(a.Passed);
            Assert.IsFalse(b.Passed);
            Assert.IsNotNull(a.Evaluation);
            Assert.IsNotNull(b.Evaluation);
            Assert.AreNotEqual(a.Evaluation.ReproductionFingerprint, b.Evaluation.ReproductionFingerprint);
            ExperimentResult? persisted = JsonSerializer.Deserialize<ExperimentResult>(
                await File.ReadAllTextAsync(b.EvidenceLocation));
            Assert.IsNotNull(persisted);
            Assert.IsFalse(persisted.Passed);
            Assert.AreEqual(0, persisted.Evaluation?.Passed);
            Assert.AreEqual(1, persisted.Evaluation?.Failed);
            Assert.IsFalse(persisted.Evaluation!.AllPassed);
            Assert.IsFalse(persisted.Evaluation!.ExactMatch);
        }
        finally
        {
            if (Directory.Exists(aDir)) Directory.Delete(aDir, true);
            if (Directory.Exists(bDir)) Directory.Delete(bDir, true);
        }
    }
}
