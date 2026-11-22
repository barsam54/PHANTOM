namespace Phantom.AgentFramework;

/// <summary>Immutable specification for a reproducible research experiment.</summary>
/// <remarks>Paths refer to configured external artifact storage, never repository-relative defaults.</remarks>
public sealed record ExperimentRequest(
    string ExperimentId,
    string CodeVersion,
    string InputSpecification,
    string ExecutionConfiguration);

/// <summary>Result record; PASS requires an explicit result and evidence location.</summary>
public sealed record ExperimentResult(
    string ExperimentId,
    string CodeVersion,
    string InputSpecification,
    string ExecutionConfiguration,
    string TestResult,
    bool Passed,
    string EvidenceLocation);

public static class ExperimentContract
{
    public static void Validate(ExperimentRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);
        Require(request.ExperimentId, nameof(request.ExperimentId));
        Require(request.CodeVersion, nameof(request.CodeVersion));
        Require(request.InputSpecification, nameof(request.InputSpecification));
        Require(request.ExecutionConfiguration, nameof(request.ExecutionConfiguration));
    }

    public static ExperimentResult Record(
        ExperimentRequest request, string testResult, bool passed, string evidenceLocation)
    {
        Validate(request);
        Require(testResult, nameof(testResult));
        Require(evidenceLocation, nameof(evidenceLocation));
        return new ExperimentResult(
            request.ExperimentId, request.CodeVersion,
            request.InputSpecification, request.ExecutionConfiguration,
            testResult, passed, evidenceLocation);
    }

    private static void Require(string value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("A non-empty value is required.", parameterName);
    }
}
