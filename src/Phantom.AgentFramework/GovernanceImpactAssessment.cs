namespace Phantom.AgentFramework;

/// <summary>
/// Deterministic, predeclared before/after change assessment.
/// This is a decision component, not a rollback executor.
/// </summary>
public static class GovernanceImpactAssessment
{
    public enum Direction { HigherIsBetter, LowerIsBetter }

    public sealed record Metric(
        string Name,
        double Before,
        double After,
        Direction Direction,
        double MaximumAllowedRegression,
        double MinimumMeaningfulImprovement = 0);

    public sealed record Outcome(
        string Comparison,
        bool EligibleForAcceptance,
        bool RollbackRequired,
        string Code,
        string Reason,
        string Action,
        string Resume,
        IReadOnlyList<string> Details);

    public static Outcome Evaluate(
        IReadOnlyList<Metric>? metrics,
        bool baselineAndCandidateComparable,
        bool mandatoryTestsPassed,
        bool independentEvidenceVerified,
        bool rollbackPlanVerified,
        string? maintenanceJustification = null)
    {
        static Outcome Deny(string comparison, string code, string reason,
            string action, bool rollback = false, IReadOnlyList<string>? details = null) =>
            new(comparison, false, rollback, code, reason, action, "impact_rollback",
                details ?? Array.Empty<string>());

        if (metrics is null || metrics.Count == 0)
            return Deny("INCONCLUSIVE", "GOV_METRICS_MISSING",
                "No frozen, predeclared before/after metrics were supplied.",
                "Define comparable metrics and hard regression limits before executing a change.");
        if (!baselineAndCandidateComparable)
            return Deny("INCONCLUSIVE", "GOV_COMPARISON_UNMATCHED",
                "Before/after observations do not use equivalent inputs and environments.",
                "Repeat the measurements under the same declared evaluation protocol.");
        if (metrics.Any(x => string.IsNullOrWhiteSpace(x.Name) ||
                !double.IsFinite(x.Before) || !double.IsFinite(x.After) ||
                !double.IsFinite(x.MaximumAllowedRegression) ||
                !double.IsFinite(x.MinimumMeaningfulImprovement) ||
                x.MaximumAllowedRegression < 0 || x.MinimumMeaningfulImprovement < 0) ||
            metrics.Select(x => x.Name).Distinct(StringComparer.Ordinal).Count() != metrics.Count)
            return Deny("INCONCLUSIVE", "GOV_METRIC_INVALID",
                "Metrics must have unique names, finite values and nonnegative frozen limits.",
                "Correct metric definitions and rerun the independent comparison.");
        if (!mandatoryTestsPassed)
            return Deny("REGRESSION", "GOV_MANDATORY_TEST_FAILURE",
                "At least one required safety, regression or acceptance test failed.",
                "Reject the candidate and restore a previously verified state as appropriate.",
                rollback: true);
        var details = new List<string>();
        bool regression = false, improved = false;
        foreach (Metric metric in metrics)
        {
            double gain = metric.Direction == Direction.HigherIsBetter
                ? metric.After - metric.Before
                : metric.Before - metric.After;
            if (!double.IsFinite(gain))
                return Deny("INCONCLUSIVE", "GOV_METRIC_OVERFLOW",
                    "The computed metric difference is outside the finite numeric range.",
                    "Use a stable normalized numeric representation for the measurement.");
            details.Add($"{metric.Name}: signed improvement={gain:R}; " +
                $"maximum allowed regression={metric.MaximumAllowedRegression:R}");
            if (gain < -metric.MaximumAllowedRegression)
                regression = true;
            if (gain > metric.MinimumMeaningfulImprovement)
                improved = true;
        }
        if (regression)
            return Deny("REGRESSION", "GOV_REGRESSION_DETECTED",
                "A predeclared hard regression limit was exceeded.",
                "Reject or revert the candidate; verify the original behavior after restoration.",
                rollback: true, details: details);
        if (!independentEvidenceVerified)
            return Deny("INCONCLUSIVE", "GOV_EVIDENCE_UNVERIFIED",
                "A coding worker cannot certify its own change effects.",
                "Attach independently verified run IDs, evidence digests and exact revisions.",
                details: details);
        if (!rollbackPlanVerified)
            return Deny("INCONCLUSIVE", "GOV_ROLLBACK_UNVERIFIED",
                "Safe recovery of the affected code, settings and external state has not been demonstrated.",
                "Prove restoration and the post-rollback smoke/regression checks in an isolated environment.",
                details: details);
        if (!improved && string.IsNullOrWhiteSpace(maintenanceJustification))
            return Deny("INCONCLUSIVE", "GOV_EQUIVALENCE_UNJUSTIFIED",
                "The measurements do not show meaningful improvement and no maintenance purpose is recorded.",
                "Record a justified refactor/maintenance goal or supply objective improvement evidence.",
                details: details);

        string comparison = improved ? "IMPROVED" : "EQUIVALENT";
        return new(comparison, true, false, "GOV_IMPACT_ACCEPTABLE",
            improved ? "Predeclared benefit observed with no forbidden regression."
                     : "Maintenance outcome justified with no forbidden regression.",
            "Continue to the other independent governance acceptance gates.",
            "acceptance", details);
    }
}
