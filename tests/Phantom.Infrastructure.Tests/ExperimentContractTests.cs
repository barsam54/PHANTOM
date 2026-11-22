using Phantom.AgentFramework;

namespace Phantom.Infrastructure.Tests;

[TestClass]
public sealed class ExperimentContractTests
{
    private static ExperimentRequest ValidRequest() =>
        new("EXP-001", "git:abc123", "symbol=XAUUSD;timeframe=M1",
            "engine=ctrader;mode=backtest");

    [TestMethod]
    public void RecordsAllBaselineEvidenceFields()
    {
        ExperimentResult result = ExperimentContract.Record(
            ValidRequest(), "4 tests passed", true, "/external/evidence/EXP-001.json");

        Assert.AreEqual("EXP-001", result.ExperimentId);
        Assert.AreEqual("git:abc123", result.CodeVersion);
        Assert.AreEqual("symbol=XAUUSD;timeframe=M1", result.InputSpecification);
        Assert.AreEqual("engine=ctrader;mode=backtest", result.ExecutionConfiguration);
        Assert.AreEqual("4 tests passed", result.TestResult);
        Assert.IsTrue(result.Passed);
        Assert.AreEqual("/external/evidence/EXP-001.json", result.EvidenceLocation);
    }

    [TestMethod]
    public void RejectsMissingInputSpecification()
    {
        ExperimentRequest request = ValidRequest() with { InputSpecification = " " };
        Assert.ThrowsExactly<ArgumentException>(() => ExperimentContract.Validate(request));
    }

    [TestMethod]
    public void RejectsMissingEvidenceLocation()
    {
        Assert.ThrowsExactly<ArgumentException>(() =>
            ExperimentContract.Record(ValidRequest(), "failed", false, ""));
    }

    [TestMethod]
    public void PreservesFailureStatus()
    {
        ExperimentResult result = ExperimentContract.Record(
            ValidRequest(), "invalid input", false, "/external/evidence/failed.json");
        Assert.IsFalse(result.Passed);
    }
}
