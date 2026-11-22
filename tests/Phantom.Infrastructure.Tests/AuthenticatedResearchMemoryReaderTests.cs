using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class AuthenticatedResearchMemoryReaderTests
{
    private static ClaimsPrincipal Principal(string? experiment, string? cutoff, bool authenticated = true)
    {
        var claims = new List<Claim>();
        if (experiment is not null)
            claims.Add(new Claim(AuthenticatedResearchMemoryReader.ExperimentClaimType, experiment));
        if (cutoff is not null)
            claims.Add(new Claim(AuthenticatedResearchMemoryReader.ResearchCutoffClaimType, cutoff));
        return new ClaimsPrincipal(new ClaimsIdentity(claims, authenticated ? "trusted-host" : null));
    }

    [TestMethod]
    public async Task AuthenticatedScopeAllowsOnlyItsOwnExperimentAndCutoff()
    {
        string root = Path.Combine(Path.GetTempPath(), "phantom-claims-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(root);
            string evidence = Path.Combine(root, "evidence.txt");
            byte[] bytes = Encoding.UTF8.GetBytes("authenticated research evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            DateTimeOffset observation = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
            DateTimeOffset cutoff = observation.AddDays(1);
            var candidate = new ResearchMemoryCandidate("exp-claims", "code-v1",
                new Uri(evidence).AbsoluteUri, Convert.ToHexString(SHA256.HashData(bytes)),
                observation, cutoff, "train", true);
            var store = new ResearchMemoryStore(Path.Combine(root, "memory"));
            await store.SaveAsync(candidate);
            var reader = new AuthenticatedResearchMemoryReader(store);

            Assert.AreEqual(candidate, await reader.ReadAsync(
                Principal("exp-claims", cutoff.ToString("O")), "exp-claims"));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reader.ReadAsync(Principal("exp-claims", cutoff.ToString("O"), false), "exp-claims"));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reader.ReadAsync(Principal("other-exp", cutoff.ToString("O")), "exp-claims"));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reader.ReadAsync(Principal("exp-claims", null), "exp-claims"));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reader.ReadAsync(Principal("exp-claims", observation.ToString("O")), "exp-claims"));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reader.ReadAsync(Principal("exp-claims", cutoff.ToOffset(TimeSpan.FromHours(2)).ToString("O")), "exp-claims"));
            await Assert.ThrowsExactlyAsync<UnauthorizedAccessException>(() =>
                reader.ReadAsync(Principal(null, cutoff.ToString("O")), "exp-claims"));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }
}
