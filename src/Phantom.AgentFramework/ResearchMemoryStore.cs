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

        // Never overwrite an existing experiment identity, including after process restart.
        await using FileStream stream = new(
            path, FileMode.CreateNew, FileAccess.Write, FileShare.None,
            bufferSize: 4096, options: FileOptions.Asynchronous);
        try
        {
            await JsonSerializer.SerializeAsync(stream,
                new StoredResearchMemory(ResearchMemoryAdmission.SchemaVersion, candidate),
                cancellationToken: cancellationToken);
            await stream.FlushAsync(cancellationToken);
        }
        catch
        {
            await stream.DisposeAsync();
            File.Delete(path);
            throw;
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

    private string PathFor(string experimentId)
    {
        if (string.IsNullOrWhiteSpace(experimentId) || !SafeId.IsMatch(experimentId))
            throw new ArgumentException("Unsafe experiment ID.", nameof(experimentId));
        return Path.Combine(directory, experimentId + ".json");
    }

    private sealed record StoredResearchMemory(int SchemaVersion, ResearchMemoryCandidate Candidate);
}
