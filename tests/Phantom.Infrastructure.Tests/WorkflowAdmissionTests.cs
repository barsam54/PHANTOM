using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class WorkflowAdmissionTests
{
    [TestMethod]
    public void ValidExperimentIsAdmitted()
    {
        var request = new ExperimentRequest("VALID-001", "git:fixed", "PHANTOM", "smoke");
        WorkflowAdmission result = WorkflowAdmissionPolicy.Check(request, "MOTNAHP", Path.GetTempPath());
        Assert.IsTrue(result.Allowed);
        Assert.IsNull(result.Denial);
    }

    [TestMethod]
    public void MissingRequestProducesStructuredDenial()
    {
        WorkflowAdmission result = WorkflowAdmissionPolicy.Check(null, "expected", Path.GetTempPath());
        Assert.IsFalse(result.Allowed);
        Assert.IsNotNull(result.Denial);
        Assert.AreEqual("REQUEST_MISSING", result.Denial.Code);
        Assert.AreEqual("admission", result.Denial.Stage);
        Assert.IsFalse(string.IsNullOrWhiteSpace(result.Denial.Reason));
        Assert.IsFalse(string.IsNullOrWhiteSpace(result.Denial.Action));
    }

    [TestMethod]
    public void RelativeEvidenceDirectoryIsRejected()
    {
        var request = new ExperimentRequest("VALID-002", "git:fixed", "PHANTOM", "smoke");
        WorkflowAdmission result = WorkflowAdmissionPolicy.Check(request, "MOTNAHP", "relative/path");
        Assert.IsFalse(result.Allowed);
        Assert.IsNotNull(result.Denial);
        Assert.AreEqual("EVIDENCE_PATH_INVALID", result.Denial.Code);
    }

    [TestMethod]
    public async Task RejectedRequestDoesNotCreateEvidence()
    {
        var request = new ExperimentRequest("INVALID-001", "git:fixed", "PHANTOM", "smoke");
        string relative = "phantom-invalid-" + Guid.NewGuid().ToString("N");
        WorkflowAdmissionException exception = await Assert.ThrowsExactlyAsync<WorkflowAdmissionException>(
            () => FirstWorkflow.RunWithEvidenceAsync(request, "MOTNAHP", relative));
        Assert.AreEqual("EVIDENCE_PATH_INVALID", exception.Denial.Code);
        Assert.IsFalse(Directory.Exists(relative));
    }
}
