using System.Runtime.Versioning;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Security.Claims;
using System.Security.Cryptography;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class ResearchSecurityBoundaryTests
{
    private sealed class FixedClock(DateTimeOffset now) : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() => now;
    }

    [TestMethod]
    public void IssuerRequiresAuthenticatedScopedIdentityAndBoundedLifetime()
    {
        DateTimeOffset now = new(2026, 11, 22, 0, 0, 0, TimeSpan.Zero);
        var clock = new FixedClock(now);
        var signer = new SignedResearchMemoryAccess(
            new ResearchMemoryStore(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"))),
            RandomNumberGenerator.GetBytes(32), clock);
        var issuer = new TrustedResearchGrantIssuer(signer, clock);
        DateTimeOffset cutoff = now.AddDays(-1);
        ClaimsPrincipal Principal(bool authenticated, string experiment) =>
            new(new ClaimsIdentity(new[]
            {
                new Claim(AuthenticatedResearchMemoryReader.ExperimentClaimType, experiment),
                new Claim(AuthenticatedResearchMemoryReader.ResearchCutoffClaimType, cutoff.ToString("O"))
            }, authenticated ? "verified-host" : null));

        string grant = issuer.Issue(Principal(true, "exp-a"), "exp-a", cutoff, TimeSpan.FromMinutes(5));
        Assert.Contains('.', grant);
        Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
            issuer.Issue(Principal(false, "exp-a"), "exp-a", cutoff, TimeSpan.FromMinutes(5)));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
            issuer.Issue(Principal(true, "exp-b"), "exp-a", cutoff, TimeSpan.FromMinutes(5)));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
            issuer.Issue(Principal(true, "exp-a"), "exp-a", now, TimeSpan.FromMinutes(5)));
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(() =>
            issuer.Issue(Principal(true, "exp-a"), "exp-a", cutoff, TimeSpan.FromHours(1)));
    }

    [TestMethod]
    [SupportedOSPlatform("linux")]
    [SupportedOSPlatform("macos")]
    public void UnixKeyAndStoragePreflightRejectPublicPermissions()
    {
        if (!OperatingSystem.IsLinux() && !OperatingSystem.IsMacOS()) return;
        string root = Path.Combine(Path.GetTempPath(), "phantom-private-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            File.SetUnixFileMode(root, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            string keyPath = Path.Combine(root, "key");
            byte[] expected = RandomNumberGenerator.GetBytes(32);
            File.WriteAllBytes(keyPath, expected);
            File.SetUnixFileMode(keyPath, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            CollectionAssert.AreEqual(expected, ResearchSigningKeyLoader.Load(keyPath));
            ResearchStorageBoundary.VerifyPrivateDirectory(root);
            File.SetUnixFileMode(keyPath, UnixFileMode.UserRead | UnixFileMode.OtherRead);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() => ResearchSigningKeyLoader.Load(keyPath));
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                ResearchStorageBoundary.VerifyPrivateDirectory(root));
            File.SetUnixFileMode(keyPath, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            File.SetUnixFileMode(root, UnixFileMode.UserRead | UnixFileMode.UserWrite |
                UnixFileMode.UserExecute | UnixFileMode.OtherExecute);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                ResearchStorageBoundary.VerifyPrivateDirectory(root));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }
    [TestMethod]
    [SupportedOSPlatform("linux")]
    [SupportedOSPlatform("macos")]
    public async Task MemoryManifestIsCreatedPrivateAndSymlinkAncestorIsRejected()
    {
        if (!OperatingSystem.IsLinux() && !OperatingSystem.IsMacOS()) return;
        string root = Path.Combine(Path.GetTempPath(), "phantom-secure-store-" + Guid.NewGuid().ToString("N"));
        string link = root + "-link";
        Directory.CreateDirectory(root);
        try
        {
            File.SetUnixFileMode(root, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            string evidence = Path.Combine(root, "proof.txt");
            byte[] bytes = System.Text.Encoding.UTF8.GetBytes("private evidence");
            await File.WriteAllBytesAsync(evidence, bytes);
            File.SetUnixFileMode(evidence, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            string memory = Path.Combine(root, "memory");
            Directory.CreateDirectory(memory);
            File.SetUnixFileMode(memory, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            DateTimeOffset observed = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
            var candidate = new ResearchMemoryCandidate("exp-private", "v1",
                new Uri(evidence).AbsoluteUri, Convert.ToHexString(SHA256.HashData(bytes)),
                observed, observed.AddDays(1), "train", true);
            await new ResearchMemoryStore(memory).SaveAsync(candidate);
            ResearchStorageBoundary.VerifyPrivateDirectory(memory);
            string manifest = Path.Combine(memory, "exp-private.json");
            UnixFileMode mode = File.GetUnixFileMode(manifest);
            Assert.AreEqual(UnixFileMode.UserRead | UnixFileMode.UserWrite, mode);

            Directory.CreateSymbolicLink(link, root);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                ResearchStorageBoundary.VerifyPrivateDirectory(Path.Combine(link, "memory")));
        }
        finally
        {
            if (Directory.Exists(link)) Directory.Delete(link);
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }

    [DllImport("libc", EntryPoint = "getuid")]
    private static extern uint GetUid();

    [TestMethod]
    [SupportedOSPlatform("linux")]
    public async Task LinuxPeerIdentityUsesKernelCredentialsNotCallerClaims()
    {
        if (!OperatingSystem.IsLinux()) return;
        string socketPath = Path.Combine(Path.GetTempPath(), "phantom-peer-" + Guid.NewGuid().ToString("N") + ".sock");
        DateTimeOffset cutoff = new(2026, 11, 21, 0, 0, 0, TimeSpan.Zero);
        using var listener = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
        listener.Bind(new UnixDomainSocketEndPoint(socketPath));
        listener.Listen(1);
        try
        {
            using var client = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
            await client.ConnectAsync(new UnixDomainSocketEndPoint(socketPath));
            using Socket accepted = await listener.AcceptAsync();
            uint uid = GetUid();
            var authorized = new LinuxPeerIdentityProvider(
                new Dictionary<uint, string> { [uid] = "exp-kernel" }, cutoff);
            ClaimsPrincipal principal = authorized.Authenticate(accepted);
            Assert.AreEqual("linux-so-peercred", principal.Identity?.AuthenticationType);
            Assert.AreEqual("exp-kernel",
                principal.FindFirst(AuthenticatedResearchMemoryReader.ExperimentClaimType)?.Value);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                new LinuxPeerIdentityProvider(new Dictionary<uint, string>(), cutoff).Authenticate(accepted));
            using var disconnected = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() => authorized.Authenticate(disconnected));
        }
        finally
        {
            if (File.Exists(socketPath)) File.Delete(socketPath);
        }
    }

    [TestMethod]
    [SupportedOSPlatform("linux")]
    public async Task LinuxGrantEndpointAuthenticatesKernelPeerBeforeIssuingScope()
    {
        if (!OperatingSystem.IsLinux()) return;
        string socketPath = Path.Combine(Path.GetTempPath(), "phantom-grant-" + Guid.NewGuid().ToString("N") + ".sock");
        DateTimeOffset now = new(2026, 11, 22, 0, 0, 0, TimeSpan.Zero);
        DateTimeOffset cutoff = now.AddDays(-1);
        var clock = new FixedClock(now);
        var signer = new SignedResearchMemoryAccess(
            new ResearchMemoryStore(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"))),
            RandomNumberGenerator.GetBytes(32), clock);
        var issuer = new TrustedResearchGrantIssuer(signer, clock);
        using var listener = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
        listener.Bind(new UnixDomainSocketEndPoint(socketPath));
        listener.Listen(1);
        try
        {
            using var client = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
            await client.ConnectAsync(new UnixDomainSocketEndPoint(socketPath));
            using Socket accepted = await listener.AcceptAsync();
            var endpoint = new LinuxResearchGrantEndpoint(
                new LinuxPeerIdentityProvider(new Dictionary<uint, string> { [GetUid()] = "exp-a" }, cutoff),
                issuer);
            string grant = endpoint.IssueForConnectedPeer(accepted, "exp-a", cutoff, TimeSpan.FromMinutes(5));
            Assert.Contains('.', grant);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                endpoint.IssueForConnectedPeer(accepted, "exp-b", cutoff, TimeSpan.FromMinutes(5)));
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                endpoint.IssueForConnectedPeer(accepted, "exp-a", now, TimeSpan.FromMinutes(5)));
            var denied = new LinuxResearchGrantEndpoint(
                new LinuxPeerIdentityProvider(new Dictionary<uint, string>(), cutoff), issuer);
            Assert.ThrowsExactly<UnauthorizedAccessException>(() =>
                denied.IssueForConnectedPeer(accepted, "exp-a", cutoff, TimeSpan.FromMinutes(5)));
        }
        finally
        {
            if (File.Exists(socketPath)) File.Delete(socketPath);
        }
    }

    [TestMethod]
    [SupportedOSPlatform("linux")]
    public async Task LinuxGrantServerReturnsGrantAndDeniesWrongExperiment()
    {
        if (!OperatingSystem.IsLinux()) return;
        string socketPath = Path.Combine(Path.GetTempPath(), "phantom-service-" + Guid.NewGuid().ToString("N") + ".sock");
        DateTimeOffset now = new(2026, 11, 22, 0, 0, 0, TimeSpan.Zero);
        DateTimeOffset cutoff = now.AddDays(-1);
        var clock = new FixedClock(now);
        var signer = new SignedResearchMemoryAccess(
            new ResearchMemoryStore(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"))),
            RandomNumberGenerator.GetBytes(32), clock);
        var server = new LinuxResearchGrantServer(new LinuxResearchGrantEndpoint(
            new LinuxPeerIdentityProvider(new Dictionary<uint, string> { [GetUid()] = "exp-a" }, cutoff),
            new TrustedResearchGrantIssuer(signer, clock)));
        using var listener = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
        listener.Bind(new UnixDomainSocketEndPoint(socketPath));
        listener.Listen(2);
        try
        {
            async Task<string> Exchange(string experiment)
            {
                using var client = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
                await client.ConnectAsync(new UnixDomainSocketEndPoint(socketPath));
                using Socket accepted = await listener.AcceptAsync();
                Task serve = server.ServeConnectionAsync(accepted);
                await using var stream = new NetworkStream(client, ownsSocket: false);
                using var reader = new StreamReader(stream);
                await using var writer = new StreamWriter(stream) { AutoFlush = true };
                await writer.WriteLineAsync(System.Text.Json.JsonSerializer.Serialize(
                    new { experimentId = experiment, cutoffUtc = cutoff }));
                string response = (await reader.ReadLineAsync()) ?? "";
                await serve;
                return response;
            }
            string allowed = await Exchange("exp-a");
            Assert.Contains("grant", allowed);
            string denied = await Exchange("exp-b");
            Assert.Contains("denied", denied);
        }
        finally
        {
            if (File.Exists(socketPath)) File.Delete(socketPath);
        }
    }

}
