using System.Security.Cryptography;
using System.Text;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class ResearchMemoryEvidenceVerifierTests
{
    private static ResearchMemoryCandidate Candidate(string path, string fingerprint) => new(
        "experiment-evidence", "commit-abc", new Uri(path).AbsoluteUri,
        fingerprint,
        new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero),
        new DateTimeOffset(2026, 1, 2, 0, 0, 0, TimeSpan.Zero),
        "train", true);

    [TestMethod]
    public async Task AcceptsEvidenceWithMatchingContentHash()
    {
        string path = Path.Combine(Path.GetTempPath(), $"phantom-memory-{Guid.NewGuid():N}.json");
        try
        {
            byte[] bytes = Encoding.UTF8.GetBytes("{\"experiment\":\"valid\"}");
            await File.WriteAllBytesAsync(path, bytes);
            await ResearchMemoryEvidenceVerifier.VerifyAsync(
                Candidate(path, Convert.ToHexString(SHA256.HashData(bytes))));
        }
        finally { File.Delete(path); }
    }

    [TestMethod]
    public async Task RejectsTamperedEvidence()
    {
        string path = Path.Combine(Path.GetTempPath(), $"phantom-memory-{Guid.NewGuid():N}.json");
        try
        {
            byte[] original = Encoding.UTF8.GetBytes("{\"experiment\":\"original\"}");
            await File.WriteAllTextAsync(path, "{\"experiment\":\"tampered\"}");
            await Assert.ThrowsExactlyAsync<InvalidDataException>(() =>
                ResearchMemoryEvidenceVerifier.VerifyAsync(
                    Candidate(path, Convert.ToHexString(SHA256.HashData(original)))));
        }
        finally { File.Delete(path); }
    }

    [TestMethod]
    public async Task RejectsMissingEvidence()
    {
        string path = Path.Combine(Path.GetTempPath(), $"phantom-memory-{Guid.NewGuid():N}.json");
        await Assert.ThrowsExactlyAsync<FileNotFoundException>(() =>
            ResearchMemoryEvidenceVerifier.VerifyAsync(
                Candidate(path, new string('A', 64))));
    }
}
