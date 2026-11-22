using System.Security.Cryptography;
using System.Text;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class SignedResearchMemoryAccessTests
{
    [TestMethod]
    public async Task SignedGrantEnforcesSignatureExperimentCutoffAndExpiry()
    {
        string root = Path.Combine(Path.GetTempPath(), "phantom-grant-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(root);
            string evidence = Path.Combine(root, "evidence.txt");
            byte[] bytes = Encoding.UTF8.GetBytes("signed grant evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            DateTimeOffset observed = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
            DateTimeOffset cutoff = observed.AddDays(1);
            DateTimeOffset now = new(2026, 11, 22, 0, 0, 0, TimeSpan.Zero);
            var candidate = new ResearchMemoryCandidate("exp-signed", "code-v1",
                new Uri(evidence).AbsoluteUri, Convert.ToHexString(SHA256.HashData(bytes)),
                observed, cutoff, "train", true);
            var store = new ResearchMemoryStore(Path.Combine(root, "memory"));
            await store.SaveAsync(candidate);
            byte[] key = RandomNumberGenerator.GetBytes(32);
            var access = new SignedResearchMemoryAccess(store, key);
            string grant = access.Issue("exp-signed", cutoff, now.AddMinutes(5));

            Assert.AreEqual(candidate, await access.ReadAsync(grant, "exp-signed", now));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                access.ReadAsync(grant, "other-exp", now));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                access.ReadAsync(grant, "exp-signed", now.AddMinutes(5)));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                new SignedResearchMemoryAccess(store, RandomNumberGenerator.GetBytes(32))
                    .ReadAsync(grant, "exp-signed", now));
            string[] parts = grant.Split('.');
            byte[] payload = Convert.FromBase64String(parts[0]);
            payload[0] ^= 1;
            string tampered = Convert.ToBase64String(payload) + "." + parts[1];
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                access.ReadAsync(tampered, "exp-signed", now));
            string earlyGrant = access.Issue("exp-signed", observed, now.AddMinutes(5));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                access.ReadAsync(earlyGrant, "exp-signed", now));
            await Assert.ThrowsExactlyAsync<ArgumentException>(() =>
                access.ReadAsync(grant, "exp-signed", now.ToOffset(TimeSpan.FromHours(1))));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }
}
