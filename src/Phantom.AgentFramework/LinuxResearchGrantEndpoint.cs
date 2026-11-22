using System.Net.Sockets;
using System.Runtime.Versioning;

namespace Phantom.AgentFramework;

/// <summary>
/// Trusted-side request handler for a connected Unix socket. The request can
/// choose a narrower cutoff but cannot supply its own identity or scope.
/// Keep this object and its signing key inside the trusted service process.
/// </summary>
[SupportedOSPlatform("linux")]
public sealed class LinuxResearchGrantEndpoint
{
    private readonly LinuxPeerIdentityProvider identities;
    private readonly TrustedResearchGrantIssuer issuer;

    public LinuxResearchGrantEndpoint(LinuxPeerIdentityProvider identities,
        TrustedResearchGrantIssuer issuer)
    {
        this.identities = identities ?? throw new ArgumentNullException(nameof(identities));
        this.issuer = issuer ?? throw new ArgumentNullException(nameof(issuer));
    }

    public string IssueForConnectedPeer(Socket acceptedSocket, string requestedExperimentId,
        DateTimeOffset requestedCutoffUtc, TimeSpan lifetime)
    {
        // Authenticate first. Never trust caller-provided ClaimsPrincipal.
        var principal = identities.Authenticate(acceptedSocket);
        return issuer.Issue(principal, requestedExperimentId, requestedCutoffUtc, lifetime);
    }
}
