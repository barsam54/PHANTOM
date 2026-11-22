using System.Security.Claims;

namespace Phantom.AgentFramework;

/// <summary>
/// Application-level policy adapter for identities authenticated by a trusted host.
/// Authentication and filesystem isolation are host responsibilities.
/// </summary>
public sealed class AuthenticatedResearchMemoryReader
{
    public const string ExperimentClaimType = "phantom:experiment";
    public const string ResearchCutoffClaimType = "phantom:research-cutoff-utc";
    private readonly ResearchMemoryStore store;

    public AuthenticatedResearchMemoryReader(ResearchMemoryStore store)
    {
        this.store = store ?? throw new ArgumentNullException(nameof(store));
    }

    public Task<ResearchMemoryCandidate> ReadAsync(
        ClaimsPrincipal principal,
        string requestedExperimentId,
        CancellationToken cancellationToken = default)
    {
        if (principal?.Identity?.IsAuthenticated != true)
            throw new UnauthorizedAccessException("An authenticated principal is required.");

        string[] experiments = principal.FindAll(ExperimentClaimType)
            .Select(static claim => claim.Value).ToArray();
        if (experiments.Length != 1 ||
            !string.Equals(experiments[0], requestedExperimentId, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("Experiment access denied.");

        string[] cutoffs = principal.FindAll(ResearchCutoffClaimType)
            .Select(static claim => claim.Value).ToArray();
        if (cutoffs.Length != 1 ||
            !DateTimeOffset.TryParseExact(cutoffs[0], "O",
                System.Globalization.CultureInfo.InvariantCulture,
                System.Globalization.DateTimeStyles.None, out DateTimeOffset cutoff) ||
            cutoff.Offset != TimeSpan.Zero)
            throw new UnauthorizedAccessException("A single valid UTC research cutoff claim is required.");

        return store.ReadForResearchAsync(requestedExperimentId, cutoff, cancellationToken);
    }
}
