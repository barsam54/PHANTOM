using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class WorkflowEvidenceTests
{
    [TestMethod]
    public async Task RecordsPassingRealWorkflowOutput()
    {
        string directory = Path.Combine(Path.GetTempPath(), "phantom-workflow-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("WF-PASS-001", "git:test", "PHANTOM", "smoke=uppercase-reverse");
            ExperimentResult result = await FirstWorkflow.RunWithEvidenceAsync(request, "MOTNAHP", directory);
            Assert.IsTrue(result.Passed);
            Assert.IsTrue(File.Exists(result.EvidenceLocation));
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
    }

    [TestMethod]
    public async Task RecordsFailedExpectationWithoutFalsePass()
    {
        string directory = Path.Combine(Path.GetTempPath(), "phantom-workflow-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("WF-FAIL-001", "git:test", "PHANTOM", "smoke=uppercase-reverse");
            ExperimentResult result = await FirstWorkflow.RunWithEvidenceAsync(request, "WRONG", directory);
            Assert.IsFalse(result.Passed);
            Assert.IsTrue(File.Exists(result.EvidenceLocation));
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
    }
}
