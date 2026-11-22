using System.Text.Json;
using System.Text.RegularExpressions;

namespace Phantom.AgentFramework;

/// <summary>
/// Immutable local research-memory manifest store. It does not orchestrate workflows.
/// The caller supplies an external storage root and must control filesystem access.
/// </summary>
public sealed class ResearchMemoryStore
{
    private static readonly Regex SafeId = new(
        "^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking);
    private readonly string directory;

    public ResearchMemoryStore(string directory)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(directory);
        if (!Path.IsPathFullyQualified(directory))
            throw new ArgumentException("Memory directory must be absolute.", nameof(directory));
        this.directory = Path.GetFullPath(directory);
    }

    public async Task SaveAsync(
        ResearchMemoryCandidate candidate,
        CancellationToken cancellationToken = default)
    {
        ResearchMemoryAdmission.Validate(candidate);
        string path = PathFor(candidate.ExperimentId);
        await ResearchMemoryEvidenceVerifier.VerifyAsync(candidate, cancellationToken);
        cancellationToken.ThrowIfCancellationRequested();
        Directory.CreateDirectory(directory);

        // Publish only complete manifests. Concurrent writers cannot overwrite an identity.
        // Temporary files may remain after a hard process kill and are never read as records.
        string temporaryPath = Path.Combine(directory, $".{candidate.ExperimentId}.{Guid.NewGuid():N}.tmp");
        try
        {
            var options = new FileStreamOptions
            {
                Mode = FileMode.CreateNew,
                Access = FileAccess.Write,
                Share = FileShare.None,
                BufferSize = 4096,
                Options = FileOptions.Asynchronous
            };
            if (OperatingSystem.IsLinux() || OperatingSystem.IsMacOS())
                options.UnixCreateMode = UnixFileMode.UserRead | UnixFileMode.UserWrite;
            await using (FileStream stream = new(temporaryPath, options))
            {
                await JsonSerializer.SerializeAsync(stream,
                    new StoredResearchMemory(ResearchMemoryAdmission.SchemaVersion, candidate),
                    cancellationToken: cancellationToken);
                await stream.FlushAsync(cancellationToken);
                stream.Flush(flushToDisk: true);
            }

            cancellationToken.ThrowIfCancellationRequested();
            File.Move(temporaryPath, path, overwrite: false);
        }
        finally
        {
            // Never delete the published record, including if a competing writer won.
            if (File.Exists(temporaryPath))
                File.Delete(temporaryPath);
        }
    }

    public async Task<ResearchMemoryCandidate> ReadAsync(
        string experimentId,
        CancellationToken cancellationToken = default)
    {
        string path = PathFor(experimentId);
        if (!Directory.Exists(directory))
            throw new FileNotFoundException("Research memory record not found.", path);
        await using FileStream stream = new(
            path, FileMode.Open, FileAccess.Read, FileShare.Read,
            bufferSize: 4096, options: FileOptions.Asynchronous);
        StoredResearchMemory? record =
            await JsonSerializer.DeserializeAsync<StoredResearchMemory>(
                stream, cancellationToken: cancellationToken);
        if (record is null || record.SchemaVersion != ResearchMemoryAdmission.SchemaVersion ||
            record.Candidate is null ||
            !string.Equals(record.Candidate.ExperimentId, experimentId, StringComparison.Ordinal))
            throw new InvalidDataException("Research memory schema or identity mismatch.");
        try
        {
            ResearchMemoryAdmission.Validate(record.Candidate);
        }
        catch (ArgumentException error)
        {
            throw new InvalidDataException("Invalid stored research memory.", error);
        }
        await ResearchMemoryEvidenceVerifier.VerifyAsync(record.Candidate, cancellationToken);
        return record.Candidate;
    }

    /// <summary>
    /// Policy-scoped retrieval for a caller whose identity was authenticated elsewhere.
    /// This is not an authentication or filesystem authorization boundary.
    /// </summary>
    public async Task<ResearchMemoryCandidate> ReadForResearchAsync(
        string experimentId,
        DateTimeOffset allowedCutoffUtc,
        CancellationToken cancellationToken = default)
    {
        if (allowedCutoffUtc.Offset != TimeSpan.Zero)
            throw new ArgumentException("Research cutoff must be UTC.", nameof(allowedCutoffUtc));

        ResearchMemoryCandidate candidate = await ReadAsync(experimentId, cancellationToken);
        if (candidate.ObservationUtc > allowedCutoffUtc ||
            candidate.ResearchCutoffUtc > allowedCutoffUtc ||
            !string.Equals(candidate.DatasetPartition, "train", StringComparison.Ordinal))
            throw new UnauthorizedAccessException("Research memory is outside the permitted cutoff or split.");

        return candidate;
    }

    /// <summary>
    /// Applies an externally established experiment scope before opening a record.
    /// The authorized ID must come from a trusted caller, never from the request itself.
    /// </summary>
    public Task<ResearchMemoryCandidate> ReadForAuthorizedExperimentAsync(
        string requestedExperimentId,
        string authorizedExperimentId,
        DateTimeOffset allowedCutoffUtc,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(authorizedExperimentId) ||
            !string.Equals(requestedExperimentId, authorizedExperimentId, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("Requested experiment is outside the authorized scope.");

        return ReadForResearchAsync(requestedExperimentId, allowedCutoffUtc, cancellationToken);
    }

    private string PathFor(string experimentId)
    {
        if (string.IsNullOrWhiteSpace(experimentId) || !SafeId.IsMatch(experimentId))
            throw new ArgumentException("Unsafe experiment ID.", nameof(experimentId));
        return Path.Combine(directory, experimentId + ".json");
    }

    private sealed record StoredResearchMemory(int SchemaVersion, ResearchMemoryCandidate Candidate);
}
