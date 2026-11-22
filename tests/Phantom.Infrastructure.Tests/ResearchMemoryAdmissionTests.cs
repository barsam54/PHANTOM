using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class ResearchMemoryAdmissionTests
{
    private static ResearchMemoryCandidate Valid() => new(
        "experiment-1", "commit-abc", "file:///tmp/phantom-evidence/experiment-1.json",
        new string('A', 64),
        new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero),
        new DateTimeOffset(2026, 1, 2, 0, 0, 0, TimeSpan.Zero),
        "train", true);

    [TestMethod]
    public void ValidTrainingObservationIsAdmissible() =>
        ResearchMemoryAdmission.Validate(Valid());

    [TestMethod]
    public void RejectsFutureObservation() =>
        Assert.ThrowsExactly<ArgumentException>(() =>
            ResearchMemoryAdmission.Validate(Valid() with
            {
                ObservationUtc = new DateTimeOffset(2026, 1, 3, 0, 0, 0, TimeSpan.Zero)
            }));

    [TestMethod]
    public void RejectsHeldOutPartition() =>
        Assert.ThrowsExactly<ArgumentException>(() =>
            ResearchMemoryAdmission.Validate(Valid() with { DatasetPartition = "test" }));

    [TestMethod]
    public void RejectsUnverifiedEvaluation() =>
        Assert.ThrowsExactly<ArgumentException>(() =>
            ResearchMemoryAdmission.Validate(Valid() with { EvaluationPassed = false }));

    [TestMethod]
    public void RejectsMissingProvenance() =>
        Assert.ThrowsExactly<ArgumentException>(() =>
            ResearchMemoryAdmission.Validate(Valid() with { EvidenceLocation = "" }));

    [TestMethod]
    public void RejectsInvalidFingerprint() =>
        Assert.ThrowsExactly<ArgumentException>(() =>
            ResearchMemoryAdmission.Validate(Valid() with { SourceFingerprint = "unknown" }));

    [TestMethod]
    public void RejectsNonUtcTimestamps() =>
        Assert.ThrowsExactly<ArgumentException>(() =>
            ResearchMemoryAdmission.Validate(Valid() with
            {
                ObservationUtc = new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.FromHours(2))
            }));
}
