using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security.Claims;

namespace Phantom.AgentFramework;

/// <summary>
/// Authenticates a connected Linux Unix-domain socket peer using kernel SO_PEERCRED.
/// Caller must enforce a separate OS UID for untrusted workers and keep the socket
/// and storage inaccessible to unauthorized UIDs. No caller-supplied identity accepted.
/// </summary>
[SupportedOSPlatform("linux")]
public sealed class LinuxPeerIdentityProvider
{
    private const int SolSocket = 1;
    private const int SoPeerCred = 17;
    private readonly IReadOnlyDictionary<uint, string> experimentByUid;
    private readonly DateTimeOffset maximumCutoffUtc;

    public LinuxPeerIdentityProvider(IReadOnlyDictionary<uint, string> experimentByUid,
        DateTimeOffset maximumCutoffUtc)
    {
        this.experimentByUid = experimentByUid ?? throw new ArgumentNullException(nameof(experimentByUid));
        if (maximumCutoffUtc.Offset != TimeSpan.Zero)
            throw new ArgumentException("Cutoff must be UTC.", nameof(maximumCutoffUtc));
        this.maximumCutoffUtc = maximumCutoffUtc;
    }

    public ClaimsPrincipal Authenticate(Socket connectedUnixSocket)
    {
        ArgumentNullException.ThrowIfNull(connectedUnixSocket);
        if (connectedUnixSocket.AddressFamily != AddressFamily.Unix || !connectedUnixSocket.Connected)
            throw new UnauthorizedAccessException("Connected Unix-domain socket required.");
        uint size = (uint)Marshal.SizeOf<PeerCredentials>();
        if (GetSockOpt(connectedUnixSocket.Handle, SolSocket, SoPeerCred,
                out PeerCredentials credentials, ref size) != 0 ||
            size != Marshal.SizeOf<PeerCredentials>())
            throw new UnauthorizedAccessException("Kernel peer credential verification failed.");
        if (!experimentByUid.TryGetValue(credentials.Uid, out string? experiment) ||
            string.IsNullOrWhiteSpace(experiment))
            throw new UnauthorizedAccessException("Peer UID not authorized.");
        var identity = new ClaimsIdentity(new[]
        {
            new Claim(ClaimTypes.NameIdentifier, credentials.Uid.ToString(System.Globalization.CultureInfo.InvariantCulture)),
            new Claim(AuthenticatedResearchMemoryReader.ExperimentClaimType, experiment),
            new Claim(AuthenticatedResearchMemoryReader.ResearchCutoffClaimType,
                maximumCutoffUtc.ToString("O", System.Globalization.CultureInfo.InvariantCulture))
        }, "linux-so-peercred");
        return new ClaimsPrincipal(identity);
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct PeerCredentials
    {
        public int Pid;
        public uint Uid;
        public uint Gid;
    }

    [DllImport("libc", EntryPoint = "getsockopt", SetLastError = true)]
    private static extern int GetSockOpt(IntPtr socket, int level, int option,
        out PeerCredentials credentials, ref uint size);
}
