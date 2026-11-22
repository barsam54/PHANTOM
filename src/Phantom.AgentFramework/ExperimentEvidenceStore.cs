using System.Text.Json;
using System.Text.RegularExpressions;

namespace Phantom.AgentFramework;

/// <summary>Writes one immutable JSON evidence record per experiment to an explicitly configured directory.</summary>
public static class ExperimentEvidenceStore
{
    private static readonly Regex SafeId = new(
        "^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$",
        RegexOptions.CultureInvariant | RegexOptions.NonBacktracking);

    public static async Task<ExperimentResult> SaveAsync(
        ExperimentRequest request,
        string testResult,
        bool passed,
        string evidenceDirectory,
        CancellationToken cancellationToken = default,
        WorkflowEvaluationEvidence? evaluation = null)
    {
        ExperimentContract.Validate(request);
        ArgumentException.ThrowIfNullOrWhiteSpace(testResult);
        ArgumentException.ThrowIfNullOrWhiteSpace(evidenceDirectory);

        if (!Path.IsPathFullyQualified(evidenceDirectory))
            throw new ArgumentException("Evidence directory must be an absolute path.", nameof(evidenceDirectory));

        if (!SafeId.IsMatch(request.ExperimentId))
            throw new ArgumentException("Experiment ID contains unsafe path characters.", nameof(request));

        string directory = Path.GetFullPath(evidenceDirectory);
        string path = Path.Combine(directory, request.ExperimentId + ".json");
        ExperimentResult result = ExperimentContract.Record(request, testResult, passed, path)
        {
            Evaluation = evaluation
        };

        cancellationToken.ThrowIfCancellationRequested();
        Directory.CreateDirectory(directory);

        // CreateNew prevents accidental overwrites; no fallback to a second record for the same ID.
        await using FileStream stream = new(
            path, FileMode.CreateNew, FileAccess.Write, FileShare.None,
            bufferSize: 4096, options: FileOptions.Asynchronous);

        try
        {
            await JsonSerializer.SerializeAsync(stream, result, cancellationToken: cancellationToken);
            await stream.FlushAsync(cancellationToken);
        }
        catch
        {
            await stream.DisposeAsync();
            File.Delete(path);
            throw;
        }

        return result;
    }
}
