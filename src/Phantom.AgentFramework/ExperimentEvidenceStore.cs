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
            with { Evaluation = evaluation };

        cancellationToken.ThrowIfCancellationRequested();
        Directory.CreateDirectory(directory);

        // Stage a complete evidence record before publishing its immutable identity.
        // A process kill during serialization leaves only an unreferenced temporary file.
        string temporaryPath = Path.Combine(directory,
            $".{request.ExperimentId}.{Guid.NewGuid():N}.tmp");
        try
        {
            await using (FileStream stream = new(
                temporaryPath, FileMode.CreateNew, FileAccess.Write, FileShare.None,
                bufferSize: 4096, options: FileOptions.Asynchronous))
            {
                await JsonSerializer.SerializeAsync(stream, result,
                    cancellationToken: cancellationToken);
                await stream.FlushAsync(cancellationToken);
                stream.Flush(flushToDisk: true);
            }

            cancellationToken.ThrowIfCancellationRequested();
            File.Move(temporaryPath, path, overwrite: false);
        }
        finally
        {
            if (File.Exists(temporaryPath))
                File.Delete(temporaryPath);
        }

        return result;
    }
}
