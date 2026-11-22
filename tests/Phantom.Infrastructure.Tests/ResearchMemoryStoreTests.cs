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
    public async Task ScopedReadRejectsFutureCutoffAndAcceptsPermittedTrainingEvidence()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-store-{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(root);
            string evidence = Path.Combine(root, "evidence.txt");
            byte[] bytes = Encoding.UTF8.GetBytes("scoped evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            var candidate = new ResearchMemoryCandidate(
                "exp-scoped", "code-v1", new Uri(evidence).AbsoluteUri,
                Convert.ToHexString(SHA256.HashData(bytes)),
                Observation, Cutoff, "train", true);
            var store = new ResearchMemoryStore(Path.Combine(root, "memory"));
            await store.SaveAsync(candidate);

            ResearchMemoryCandidate result =
                await store.ReadForResearchAsync("exp-scoped", Cutoff);
            Assert.AreEqual(candidate, result);

            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                store.ReadForResearchAsync("exp-scoped", Observation));
            await Assert.ThrowsExactlyAsync<ArgumentException>(() =>
                store.ReadForResearchAsync("exp-scoped",
                    new DateTimeOffset(2026, 1, 3, 0, 0, 0, TimeSpan.FromHours(2))));
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, recursive: true); }
    }

    [TestMethod]
    public async Task AuthorizedExperimentReadRejectsCrossExperimentAccess()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-store-{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(root);
            string evidence = Path.Combine(root, "evidence.txt");
            byte[] bytes = Encoding.UTF8.GetBytes("experiment scoped evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            var candidate = new ResearchMemoryCandidate(
                "exp-a", "code-v1", new Uri(evidence).AbsoluteUri,
                Convert.ToHexString(SHA256.HashData(bytes)),
                Observation, Cutoff, "train", true);
            var store = new ResearchMemoryStore(Path.Combine(root, "memory"));
            await store.SaveAsync(candidate);

            ResearchMemoryCandidate result =
                await store.ReadForAuthorizedExperimentAsync("exp-a", "exp-a", Cutoff);
            Assert.AreEqual(candidate, result);

            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                store.ReadForAuthorizedExperimentAsync("exp-a", "exp-b", Cutoff));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                store.ReadForAuthorizedExperimentAsync("exp-a", "", Cutoff));
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, recursive: true); }
    }

    [TestMethod]
    public async Task AtomicPublishIgnoresOrphanTempFilesAndRejectsDuplicate()
    {
        string root = Path.Combine(Path.GetTempPath(), $"phantom-atomic-{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(root);
            string evidence = Path.Combine(root, "evidence.txt");
            byte[] bytes = Encoding.UTF8.GetBytes("atomic evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            string memory = Path.Combine(root, "memory");
            Directory.CreateDirectory(memory);
            await File.WriteAllTextAsync(Path.Combine(memory, ".exp-atomic.interrupted.tmp"),
                "{\"SchemaVersion\":1,");
            var candidate = new ResearchMemoryCandidate(
                "exp-atomic", "code-v1", new Uri(evidence).AbsoluteUri,
                Convert.ToHexString(SHA256.HashData(bytes)),
                Observation, Cutoff, "train", true);
            var store = new ResearchMemoryStore(memory);
            await Assert.ThrowsExactlyAsync<FileNotFoundException>(() => store.ReadAsync("exp-atomic"));
            await store.SaveAsync(candidate);
            Assert.AreEqual(candidate, await store.ReadAsync("exp-atomic"));
            await Assert.ThrowsExactlyAsync<IOException>(() => store.SaveAsync(candidate));
            Assert.AreEqual(candidate, await store.ReadAsync("exp-atomic"));
            Assert.IsTrue(File.Exists(Path.Combine(memory, ".exp-atomic.interrupted.tmp")));
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
