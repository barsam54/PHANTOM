using System.Text.Json;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class ExperimentEvidenceStoreTests
{
    private static ExperimentRequest Request(string id = "EXP-STORE-001") =>
        new(id, "git:abc123", "symbol=XAUUSD;timeframe=M1", "mode=backtest");

    [TestMethod]
    public async Task WritesAndReadsEvidenceRecord()
    {
        string directory = Path.Combine(Path.GetTempPath(), "phantom-evidence-" + Guid.NewGuid().ToString("N"));
        try
        {
            ExperimentResult result = await ExperimentEvidenceStore.SaveAsync(
                Request(), "tests passed", true, directory);
            Assert.IsTrue(File.Exists(result.EvidenceLocation));
            string json = await File.ReadAllTextAsync(result.EvidenceLocation);
            ExperimentResult? restored = JsonSerializer.Deserialize<ExperimentResult>(json);
            Assert.IsNotNull(restored);
            Assert.AreEqual(result, restored);
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true); }
    }

    [TestMethod]
    public async Task RefusesToOverwriteExistingExperiment()
    {
        string directory = Path.Combine(Path.GetTempPath(), "phantom-evidence-" + Guid.NewGuid().ToString("N"));
        try
        {
            await ExperimentEvidenceStore.SaveAsync(Request(), "first", true, directory);
            await Assert.ThrowsExactlyAsync<IOException>(() =>
                ExperimentEvidenceStore.SaveAsync(Request(), "second", false, directory));
            string json = await File.ReadAllTextAsync(Path.Combine(directory, "EXP-STORE-001.json"));
            StringAssert.Contains(json, "first");
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true); }
    }

    [TestMethod]
    public async Task RejectsUnsafeExperimentId()
    {
        string directory = Path.Combine(Path.GetTempPath(), "phantom-evidence-" + Guid.NewGuid().ToString("N"));
        await Assert.ThrowsExactlyAsync<ArgumentException>(() =>
            ExperimentEvidenceStore.SaveAsync(Request("../escape"), "failed", false, directory));
        Assert.IsFalse(Directory.Exists(directory));
    }

    [TestMethod]
    public async Task RejectsRelativeStoragePath()
    {
        await Assert.ThrowsExactlyAsync<ArgumentException>(() =>
            ExperimentEvidenceStore.SaveAsync(Request(), "failed", false, "artifacts"));
    }
    [TestMethod]
    public async Task PublishesCompleteEvidenceDespiteOrphanTempAndRejectsDuplicate()
    {
        string directory = Path.Combine(Path.GetTempPath(),
            "phantom-evidence-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(directory);
            string orphan = Path.Combine(directory,
                ".EXP-STORE-001.abandoned.tmp");
            await File.WriteAllTextAsync(orphan, "{\"ExperimentId\":");
            string final = Path.Combine(directory, "EXP-STORE-001.json");
            Assert.IsFalse(File.Exists(final));

            ExperimentResult saved = await ExperimentEvidenceStore.SaveAsync(
                Request(), "evaluated", true, directory);
            Assert.AreEqual(final, saved.EvidenceLocation);
            ExperimentResult? restored = JsonSerializer.Deserialize<ExperimentResult>(
                await File.ReadAllTextAsync(final));
            Assert.IsNotNull(restored);
            Assert.AreEqual(saved, restored);
            Assert.IsTrue(File.Exists(orphan));

            await Assert.ThrowsExactlyAsync<IOException>(() =>
                ExperimentEvidenceStore.SaveAsync(
                    Request(), "must not replace", false, directory));
            ExperimentResult? afterDuplicate = JsonSerializer.Deserialize<ExperimentResult>(
                await File.ReadAllTextAsync(final));
            Assert.AreEqual(saved, afterDuplicate);
            Assert.HasCount(2, Directory.GetFiles(directory));
        }
        finally
        {
            if (Directory.Exists(directory))
                Directory.Delete(directory, recursive: true);
        }
    }

}
