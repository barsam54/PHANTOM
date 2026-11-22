using System.Security.Claims;

namespace Phantom.AgentFramework;

/// <summary>
/// Trusted-host boundary for issuing scoped grants. The host MUST authenticate the
/// principal through a verified provider before invoking this component.
/// </summary>
public sealed class TrustedResearchGrantIssuer
{
    private readonly SignedResearchMemoryAccess signer;
    private readonly TimeProvider clock;

    public TrustedResearchGrantIssuer(SignedResearchMemoryAccess signer, TimeProvider? clock = null)
    {
        this.signer = signer ?? throw new ArgumentNullException(nameof(signer));
        this.clock = clock ?? TimeProvider.System;
    }

    public string Issue(ClaimsPrincipal principal, string requestedExperimentId,
        DateTimeOffset cutoffUtc, TimeSpan lifetime)
    {
        if (principal?.Identity?.IsAuthenticated != true)
            throw new UnauthorizedAccessException("Trusted authentication required.");
        string[] scopes = principal.FindAll(AuthenticatedResearchMemoryReader.ExperimentClaimType)
            .Select(static claim => claim.Value).ToArray();
        if (scopes.Length != 1 ||
            !string.Equals(scopes[0], requestedExperimentId, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("Experiment scope denied.");
        string[] cutoffs = principal.FindAll(AuthenticatedResearchMemoryReader.ResearchCutoffClaimType)
            .Select(static claim => claim.Value).ToArray();
        if (cutoffs.Length != 1 ||
            !DateTimeOffset.TryParseExact(cutoffs[0], "O",
                System.Globalization.CultureInfo.InvariantCulture,
                System.Globalization.DateTimeStyles.None, out var authorizedCutoff) ||
            authorizedCutoff.Offset != TimeSpan.Zero ||
            cutoffUtc.Offset != TimeSpan.Zero || cutoffUtc > authorizedCutoff)
            throw new UnauthorizedAccessException("Research cutoff denied.");
        if (lifetime <= TimeSpan.Zero || lifetime > TimeSpan.FromMinutes(15))
            throw new ArgumentOutOfRangeException(nameof(lifetime), "Grant lifetime must be at most 15 minutes.");
        return signer.Issue(requestedExperimentId, cutoffUtc, clock.GetUtcNow().Add(lifetime));
    }
}
