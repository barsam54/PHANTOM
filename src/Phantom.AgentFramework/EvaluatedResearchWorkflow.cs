using System.Security.Cryptography;

namespace Phantom.AgentFramework;

/// <summary>
/// Explicit opt-in path from an evaluated Agent Framework workflow to durable research memory.
/// It does not grant authorization or promote observations into learning.
/// </summary>
public static class EvaluatedResearchWorkflow
{
    public static async Task<ExperimentResult> RunAndRememberAsync(
        ExperimentRequest request,
        string expectedOutput,
        string evidenceDirectory,
        string memoryDirectory,
        DateTimeOffset observationUtc,
        DateTimeOffset researchCutoffUtc,
        CancellationToken cancellationToken = default)
    {
        ExperimentContract.Validate(request);
        ArgumentException.ThrowIfNullOrWhiteSpace(evidenceDirectory);
        if (!Path.IsPathFullyQualified(evidenceDirectory))
            throw new ArgumentException("Evidence directory must be absolute.", nameof(evidenceDirectory));
        ArgumentException.ThrowIfNullOrWhiteSpace(memoryDirectory);
        if (!Path.IsPathFullyQualified(memoryDirectory))
            throw new ArgumentException("Memory directory must be absolute.", nameof(memoryDirectory));

        // Fail closed before execution for an ineligible research observation.
        var preflight = new ResearchMemoryCandidate(
            request.ExperimentId, request.CodeVersion,
            new Uri(Path.GetFullPath(Path.Combine(
                Path.GetFullPath(evidenceDirectory), request.ExperimentId + ".json"))).AbsoluteUri,
            new string('0', 64), observationUtc, researchCutoffUtc, "train", true);
        ResearchMemoryAdmission.Validate(preflight);

        ExperimentResult result = await FirstWorkflow.RunWithEvidenceAsync(
            request, expectedOutput, evidenceDirectory, cancellationToken);
        if (!result.Passed || result.Evaluation is null ||
            !result.Evaluation.AllPassed || !result.Evaluation.ExactMatch)
            return result; // Failed evaluations remain evidence, never training memory.

        string evidencePath = Path.GetFullPath(result.EvidenceLocation);
        await using FileStream stream = new(
            evidencePath, FileMode.Open, FileAccess.Read, FileShare.Read,
            bufferSize: 4096, options: FileOptions.Asynchronous);
        string fingerprint = Convert.ToHexString(
            await SHA256.HashDataAsync(stream, cancellationToken));
        var candidate = new ResearchMemoryCandidate(
            request.ExperimentId, request.CodeVersion, new Uri(evidencePath).AbsoluteUri,
            fingerprint, observationUtc, researchCutoffUtc, "train", true);
        await new ResearchMemoryStore(memoryDirectory).SaveAsync(candidate, cancellationToken);
        return result;
    }
}
