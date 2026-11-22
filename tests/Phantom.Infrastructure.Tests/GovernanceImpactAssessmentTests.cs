using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class GovernanceImpactAssessmentTests
{
    private static GovernanceImpactAssessment.Metric ErrorRate(double before, double after) =>
        new("error-rate", before, after,
            GovernanceImpactAssessment.Direction.LowerIsBetter,
            MaximumAllowedRegression: 0.01, MinimumMeaningfulImprovement: 0.001);

    [TestMethod]
    public void AcceptsVerifiedMeaningfulImprovement()
    {
        var result = GovernanceImpactAssessment.Evaluate([ErrorRate(.15, .08)],
            true, true, true, true);
        Assert.AreEqual("IMPROVED", result.Comparison);
        Assert.IsTrue(result.EligibleForAcceptance);
        Assert.IsFalse(result.RollbackRequired);
    }

    [TestMethod]
    public void RejectsHardRegressionAndRequiresRollback()
    {
        var result = GovernanceImpactAssessment.Evaluate([ErrorRate(.10, .20)],
            true, true, true, true);
        Assert.AreEqual("REGRESSION", result.Comparison);
        Assert.IsFalse(result.EligibleForAcceptance);
        Assert.IsTrue(result.RollbackRequired);
        Assert.AreEqual("GOV_REGRESSION_DETECTED", result.Code);
    }

    [TestMethod]
    public void MandatoryTestFailureOverridesMeasuredImprovement()
    {
        var result = GovernanceImpactAssessment.Evaluate([ErrorRate(.15, .08)],
            true, false, true, true);
        Assert.AreEqual("REGRESSION", result.Comparison);
        Assert.IsFalse(result.EligibleForAcceptance);
        Assert.IsTrue(result.RollbackRequired);
    }

    [TestMethod]
    public void MissingIndependentProofCannotSelfApprove()
    {
        var result = GovernanceImpactAssessment.Evaluate([ErrorRate(.15, .08)],
            true, true, false, true);
        Assert.AreEqual("INCONCLUSIVE", result.Comparison);
        Assert.AreEqual("GOV_EVIDENCE_UNVERIFIED", result.Code);
    }

    [TestMethod]
    public void MissingRollbackProofBlocksOtherwiseGoodChange()
    {
        var result = GovernanceImpactAssessment.Evaluate([ErrorRate(.15, .08)],
            true, true, true, false);
        Assert.AreEqual("INCONCLUSIVE", result.Comparison);
        Assert.AreEqual("GOV_ROLLBACK_UNVERIFIED", result.Code);
    }

    [TestMethod]
    public void EquivalenceAllowedOnlyWithJustification()
    {
        var denied = GovernanceImpactAssessment.Evaluate([ErrorRate(.10, .10)],
            true, true, true, true);
        Assert.IsFalse(denied.EligibleForAcceptance);
        var permitted = GovernanceImpactAssessment.Evaluate([ErrorRate(.10, .10)],
            true, true, true, true, "Behavior-preserving maintenance");
        Assert.AreEqual("EQUIVALENT", permitted.Comparison);
        Assert.IsTrue(permitted.EligibleForAcceptance);
    }

    [TestMethod]
    public void InvalidOrUnmatchedEvidenceCannotApprove()
    {
        var noMetric = GovernanceImpactAssessment.Evaluate([], true, true, true, true);
        Assert.AreEqual("INCONCLUSIVE", noMetric.Comparison);
        var unmatched = GovernanceImpactAssessment.Evaluate([ErrorRate(.15, .08)],
            false, true, true, true);
        Assert.AreEqual("GOV_COMPARISON_UNMATCHED", unmatched.Code);
        var duplicate = GovernanceImpactAssessment.Evaluate(
            [ErrorRate(.15, .08), ErrorRate(.12, .05)],
            true, true, true, true);
        Assert.AreEqual("GOV_METRIC_INVALID", duplicate.Code);
    }

    [TestMethod]
    public void RegressionOnAnyMetricCannotBeHiddenByLargeGainElsewhere()
    {
        var metrics = new[]
        {
            new GovernanceImpactAssessment.Metric("throughput", 100, 300,
                GovernanceImpactAssessment.Direction.HigherIsBetter, 10),
            ErrorRate(.05, .30)
        };
        var result = GovernanceImpactAssessment.Evaluate(metrics, true, true, true, true);
        Assert.AreEqual("REGRESSION", result.Comparison);
        Assert.IsFalse(result.EligibleForAcceptance);
    }
}
