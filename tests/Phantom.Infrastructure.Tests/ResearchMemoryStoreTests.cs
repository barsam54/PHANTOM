using System.Security.Cryptography;
using System.Text;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class ResearchMemoryStoreTests
{
    private static readonly DateTimeOffset Observation = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
    private static readonly DateTimeOffset Cutoff = new(2026, 1, 2, 0, 0, 0, TimeSpan.Zero);

    [TestMethod]
    public async Task PersistsAndReadsValidatedManifestAcrossStoreInstances()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-store-{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(root);
            string evidence = Path.Combine(root, "evidence.txt");
            byte[] bytes = Encoding.UTF8.GetBytes("verified research evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            var candidate = new ResearchMemoryCandidate(
                "exp-1", "code-v1", new Uri(evidence).AbsoluteUri,
                Convert.ToHexString(SHA256.HashData(bytes)),
                Observation, Cutoff, "train", true);
            await new ResearchMemoryStore(Path.Combine(root, "memory")).SaveAsync(candidate);
            ResearchMemoryCandidate restored =
                await new ResearchMemoryStore(Path.Combine(root, "memory")).ReadAsync("exp-1");
            Assert.AreEqual(candidate, restored);

            await Assert.ThrowsExactlyAsync<IOException>(() =>
                new ResearchMemoryStore(Path.Combine(root, "memory")).SaveAsync(candidate));

            await File.WriteAllTextAsync(evidence, "tampered");
            await Assert.ThrowsExactlyAsync<InvalidDataException>(() =>
                new ResearchMemoryStore(Path.Combine(root, "memory")).ReadAsync("exp-1"));
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, recursive: true); }
    }

    [TestMethod]
    public async Task RejectsInvalidAndUnrelatedExperimentIds()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-store-{Guid.NewGuid():N}");
        try
        {
            var store = new ResearchMemoryStore(root);
            await Assert.ThrowsExactlyAsync<ArgumentException>(() => store.ReadAsync("../outside"));
            await Assert.ThrowsExactlyAsync<FileNotFoundException>(() => store.ReadAsync("other-exp"));
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, recursive: true); }
    }

    [TestMethod]
    public async Task RejectsUnsupportedSchema()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-store-{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(root);
            await File.WriteAllTextAsync(Path.Combine(root, "exp-1.json"),
                "{\"SchemaVersion\":999,\"Candidate\":null}");
            await Assert.ThrowsExactlyAsync<InvalidDataException>(() =>
                new ResearchMemoryStore(root).ReadAsync("exp-1"));
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, recursive: true); }
    }
}
