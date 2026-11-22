namespace Phantom.AgentFramework;

/// <summary>Machine-readable refusal when an experiment cannot start safely.</summary>
public sealed record WorkflowDenial(
    string Code,
    string Stage,
    string Reason,
    string Action,
    string? Evidence = null);

public sealed record WorkflowAdmission(bool Allowed, WorkflowDenial? Denial)
{
    public static WorkflowAdmission Permit() => new(true, null);
    public static WorkflowAdmission Reject(string code, string reason, string action) =>
        new(false, new WorkflowDenial(code, "admission", reason, action));
}

/// <summary>Pure admission policy; does not create a second workflow orchestrator.</summary>
public static class WorkflowAdmissionPolicy
{
    public static WorkflowAdmission Check(ExperimentRequest? request, string? expectedOutput, string? evidenceDirectory)
    {
        if (request is null)
            return WorkflowAdmission.Reject("REQUEST_MISSING", "Experiment request is missing.", "Provide an experiment request.");
        if (string.IsNullOrWhiteSpace(request.ExperimentId) ||
            string.IsNullOrWhiteSpace(request.CodeVersion) ||
            string.IsNullOrWhiteSpace(request.InputSpecification) ||
            string.IsNullOrWhiteSpace(request.ExecutionConfiguration))
            return WorkflowAdmission.Reject("REQUEST_INVALID", "Required experiment fields are missing.", "Supply nonempty experiment ID, code version, input and configuration.");
        if (expectedOutput is null)
            return WorkflowAdmission.Reject("EXPECTED_OUTPUT_MISSING", "Expected output is missing.", "Supply an expected output.");
        if (string.IsNullOrWhiteSpace(evidenceDirectory) || !Path.IsPathFullyQualified(evidenceDirectory))
            return WorkflowAdmission.Reject("EVIDENCE_PATH_INVALID", "Evidence directory must be an absolute path.", "Configure an external absolute evidence directory.");
        return WorkflowAdmission.Permit();
    }
}

public sealed class WorkflowAdmissionException(WorkflowDenial denial) : InvalidOperationException(denial.Reason)
{
    public WorkflowDenial Denial { get; } = denial;
}
