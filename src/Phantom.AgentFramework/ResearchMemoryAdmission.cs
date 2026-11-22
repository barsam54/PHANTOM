namespace Phantom.AgentFramework;

/// <summary>
/// Admission contract for future durable research memory. This is a policy,
/// not a persistence engine or a second workflow orchestrator.
/// </summary>
public sealed record ResearchMemoryCandidate(
    string ExperimentId,
    string CodeVersion,
    string EvidenceLocation,
    string SourceFingerprint,
    DateTimeOffset ObservationUtc,
    DateTimeOffset ResearchCutoffUtc,
    string DatasetPartition,
    bool EvaluationPassed);

public static class ResearchMemoryAdmission
{
    public const int SchemaVersion = 1;

    public static void Validate(ResearchMemoryCandidate candidate)
    {
        ArgumentNullException.ThrowIfNull(candidate);
        Require(candidate.ExperimentId, nameof(candidate.ExperimentId));
        Require(candidate.CodeVersion, nameof(candidate.CodeVersion));
        Require(candidate.EvidenceLocation, nameof(candidate.EvidenceLocation));
        Require(candidate.SourceFingerprint, nameof(candidate.SourceFingerprint));
        Require(candidate.DatasetPartition, nameof(candidate.DatasetPartition));

        if (!Uri.TryCreate(candidate.EvidenceLocation, UriKind.Absolute, out Uri? evidence) ||
            evidence.Scheme != Uri.UriSchemeFile)
            throw new ArgumentException("Evidence location must be an absolute file URI.",
                nameof(candidate));

        if (candidate.SourceFingerprint.Length != 64 ||
            !candidate.SourceFingerprint.All(static c =>
                c is >= '0' and <= '9' or >= 'A' and <= 'F' or >= 'a' and <= 'f'))
            throw new ArgumentException("Source fingerprint must be SHA-256 hex.",
                nameof(candidate));

        if (candidate.ObservationUtc.Offset != TimeSpan.Zero ||
            candidate.ResearchCutoffUtc.Offset != TimeSpan.Zero)
            throw new ArgumentException("Observation and cutoff must be UTC.", nameof(candidate));

        if (candidate.ObservationUtc > candidate.ResearchCutoffUtc)
            throw new ArgumentException("Future observations cannot enter research memory.",
                nameof(candidate));

        if (!string.Equals(candidate.DatasetPartition, "train", StringComparison.Ordinal))
            throw new ArgumentException("Only explicitly designated training observations are admissible.",
                nameof(candidate));

        if (!candidate.EvaluationPassed)
            throw new ArgumentException("Failed or unverified evaluation cannot enter research memory.",
                nameof(candidate));
    }

    private static void Require(string? value, string name)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Required provenance is missing.", name);
    }
}
