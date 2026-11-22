using System.Globalization;
using System.Security.Cryptography;
using System.Text;

namespace Phantom.AgentFramework;

/// <summary>
/// Verifies host-issued, HMAC-SHA256 signed and expiring experiment-scoped read grants.
/// The issuer must keep its signing key outside the repository and outside untrusted callers.
/// </summary>
public sealed class SignedResearchMemoryAccess
{
    private readonly byte[] key;
    private readonly ResearchMemoryStore store;
    private readonly TimeProvider clock;

    public SignedResearchMemoryAccess(ResearchMemoryStore store, byte[] signingKey,
        TimeProvider? clock = null)
    {
        this.store = store ?? throw new ArgumentNullException(nameof(store));
        ArgumentNullException.ThrowIfNull(signingKey);
        if (signingKey.Length < 32)
            throw new ArgumentException("Signing key must contain at least 32 bytes.", nameof(signingKey));
        key = (byte[])signingKey.Clone();
        this.clock = clock ?? TimeProvider.System;
    }

    /// <summary>Trusted-host-only operation. Never expose this method to untrusted request handlers.</summary>
    public string Issue(string experimentId, DateTimeOffset cutoffUtc,
        DateTimeOffset expiresUtc)
    {
        ValidateGrant(experimentId, cutoffUtc, expiresUtc);
        string payload = string.Join("|", "v1", experimentId,
            cutoffUtc.UtcTicks.ToString(CultureInfo.InvariantCulture),
            expiresUtc.UtcTicks.ToString(CultureInfo.InvariantCulture));
        byte[] payloadBytes = Encoding.UTF8.GetBytes(payload);
        byte[] signature = HMACSHA256.HashData(key, payloadBytes);
        return Convert.ToBase64String(payloadBytes) + "." + Convert.ToBase64String(signature);
    }

    public Task<ResearchMemoryCandidate> ReadAsync(string grant, string requestedExperimentId,
        CancellationToken cancellationToken = default)
    {
        DateTimeOffset nowUtc = clock.GetUtcNow();
        if (string.IsNullOrWhiteSpace(grant))
            throw new UnauthorizedAccessException("Missing signed research grant.");

        string[] parts = grant.Split('.');
        if (parts.Length != 2)
            throw new UnauthorizedAccessException("Invalid research grant.");
        byte[] payload;
        byte[] signature;
        try
        {
            payload = Convert.FromBase64String(parts[0]);
            signature = Convert.FromBase64String(parts[1]);
        }
        catch (FormatException)
        {
            throw new UnauthorizedAccessException("Invalid research grant encoding.");
        }
        byte[] expected = HMACSHA256.HashData(key, payload);
        if (!CryptographicOperations.FixedTimeEquals(signature, expected))
            throw new UnauthorizedAccessException("Invalid research grant signature.");

        string[] fields = Encoding.UTF8.GetString(payload).Split('|');
        if (fields.Length != 4 || fields[0] != "v1" ||
            !string.Equals(fields[1], requestedExperimentId, StringComparison.Ordinal) ||
            !long.TryParse(fields[2], NumberStyles.None, CultureInfo.InvariantCulture, out long cutoffTicks) ||
            !long.TryParse(fields[3], NumberStyles.None, CultureInfo.InvariantCulture, out long expiryTicks) ||
            cutoffTicks < DateTime.MinValue.Ticks || cutoffTicks > DateTime.MaxValue.Ticks ||
            expiryTicks < DateTime.MinValue.Ticks || expiryTicks > DateTime.MaxValue.Ticks)
            throw new UnauthorizedAccessException("Research grant scope invalid.");

        var cutoff = new DateTimeOffset(cutoffTicks, TimeSpan.Zero);
        var expires = new DateTimeOffset(expiryTicks, TimeSpan.Zero);
        if (expires <= nowUtc || expires <= cutoff)
            throw new UnauthorizedAccessException("Research grant expired or invalid.");

        return store.ReadForResearchAsync(requestedExperimentId, cutoff, cancellationToken);
    }

    private static void ValidateGrant(string experimentId, DateTimeOffset cutoff, DateTimeOffset expires)
    {
        if (string.IsNullOrWhiteSpace(experimentId) ||
            experimentId.Contains('|') || experimentId.Contains('.'))
            throw new ArgumentException("Invalid experiment scope.", nameof(experimentId));
        if (cutoff.Offset != TimeSpan.Zero || expires.Offset != TimeSpan.Zero ||
            expires <= cutoff)
            throw new ArgumentException("Grant times must be UTC with expiry after cutoff.");
    }
}
