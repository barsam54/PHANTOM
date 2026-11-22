using System.Security.Cryptography;

namespace Phantom.AgentFramework;

/// <summary>Checks the referenced evidence bytes before memory admission.</summary>
public static class ResearchMemoryEvidenceVerifier
{
    public static async Task VerifyAsync(
        ResearchMemoryCandidate candidate,
        CancellationToken cancellationToken = default)
    {
        ResearchMemoryAdmission.Validate(candidate);
        Uri uri = new(candidate.EvidenceLocation, UriKind.Absolute);
        if (!uri.IsFile || !Path.IsPathFullyQualified(uri.LocalPath))
            throw new ArgumentException("Evidence must be an absolute local file.", nameof(candidate));

        string path = Path.GetFullPath(uri.LocalPath);
        await using FileStream stream = new(
            path, FileMode.Open, FileAccess.Read, FileShare.Read,
            bufferSize: 4096, options: FileOptions.Asynchronous);
        byte[] actual = await SHA256.HashDataAsync(stream, cancellationToken);
        byte[] expected = Convert.FromHexString(candidate.SourceFingerprint);
        if (!CryptographicOperations.FixedTimeEquals(actual, expected))
            throw new InvalidDataException("Evidence content fingerprint mismatch.");
    }
}
