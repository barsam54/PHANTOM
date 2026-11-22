using System.Diagnostics;
using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class WorkflowObservabilityTests
{
    [TestMethod]
    public async Task PassingWorkflowEmitsCorrelatedTraceWithoutInputPayload()
    {
        var completed = new List<Activity>();
        using var listener = new ActivityListener
        {
            ShouldListenTo = source => source.Name == FirstWorkflow.ActivitySourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllDataAndRecorded,
            ActivityStopped = activity => completed.Add(activity)
        };
        ActivitySource.AddActivityListener(listener);
        string directory = Path.Combine(Path.GetTempPath(), "phantom-trace-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("TRACE-001", "git:test", "PHANTOM", "smoke");
            ExperimentResult result = await FirstWorkflow.RunWithEvidenceAsync(request, "MOTNAHP", directory);
            Assert.IsTrue(result.Passed);
            Activity trace = completed.Single(activity => activity.OperationName == "phantom.experiment.evaluate");
            Assert.AreEqual("TRACE-001", trace.GetTagItem("phantom.experiment.id"));
            Assert.AreEqual(true, trace.GetTagItem("phantom.evaluation.passed"));
            Assert.AreEqual(ActivityStatusCode.Ok, trace.Status);
            Assert.IsFalse(trace.TagObjects.Any(tag => tag.Value?.ToString()?.Contains("MOTNAHP", StringComparison.Ordinal) == true));
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
    }

    [TestMethod]
    public async Task FailedEvaluationEmitsErrorTrace()
    {
        var completed = new List<Activity>();
        using var listener = new ActivityListener
        {
            ShouldListenTo = source => source.Name == FirstWorkflow.ActivitySourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllDataAndRecorded,
            ActivityStopped = activity => completed.Add(activity)
        };
        ActivitySource.AddActivityListener(listener);
        string directory = Path.Combine(Path.GetTempPath(), "phantom-trace-" + Guid.NewGuid().ToString("N"));
        try
        {
            var request = new ExperimentRequest("TRACE-FAIL-001", "git:test", "PHANTOM", "smoke");
            ExperimentResult result = await FirstWorkflow.RunWithEvidenceAsync(request, "WRONG", directory);
            Assert.IsFalse(result.Passed);
            Activity trace = completed.Single(activity => activity.OperationName == "phantom.experiment.evaluate");
            Assert.AreEqual(false, trace.GetTagItem("phantom.evaluation.passed"));
            Assert.AreEqual(ActivityStatusCode.Error, trace.Status);
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
    }
}
