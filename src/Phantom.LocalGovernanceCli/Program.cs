using Phantom.AgentFramework;
using System.Diagnostics;
using System.Text.Json;

const string profile = "infra/local-models/ollama-qwen3-4b.json";
try
{
    string root = FindRepositoryRoot();
    var config = GovernanceLocalProposalAgent.ReadConfiguration(Path.Combine(root, profile));
    if (args.Length == 1 && args[0] == "--check-profile")
    {
        Console.WriteLine("PROFILE_VALID; LOCAL_RUNTIME_NOT_CHECKED; MODEL=qwen3:4b; ACTIONS_DISABLED");
        return 0;
    }

    if (args.Length == 2 && args[0] == "--evidence-report")
    {
        // An externally generated report is untrusted until its identifiers are
        // independently compared to the checked-out source by GovEvidence.
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(args[1]));
        JsonElement input = document.RootElement;
        string Field(string key) => input.GetProperty(key).GetString()
            ?? throw new InvalidOperationException("GOV_EVIDENCE_FIELD_MISSING: " + key);
        int Number(string key) => input.GetProperty(key).GetInt32();
        bool Flag(string key) => input.GetProperty(key).GetBoolean();
        var evidence = new GovernancePhaseWorkflow.EvidenceSubmission(
            Field("schema_version"), Field("status"), Field("source_sha"),
            Field("contract_sha256"), Field("baseline_sha256"), Field("contract_gate"),
            Field("reuse_decision"), Number("criteria_discovered"),
            Number("historical_ci_criteria_verified"), Number("current_phase_criteria_verified"),
            Flag("phase_evidence_verification_completed"), Field("governance_acceptance"));
        string revision = GetCleanRepositoryRevision(root);
        var evidenceWorkflowReport = await GovernancePhaseWorkflow.RunAsync(
            root, revision, externalEvidence: evidence);
        Console.WriteLine(JsonSerializer.Serialize(evidenceWorkflowReport,
            new JsonSerializerOptions { WriteIndented = true }));
        return evidenceWorkflowReport.Steps[6].Status == "SCOPED_ONLY" &&
            !evidenceWorkflowReport.Accepted ? 0 : 2;
    }

    if (args.Length == 2 &&
        args[0] is "--checkpoint-capture" or "--checkpoint-resume")
    {
        string checkpointRevision = GetCleanRepositoryRevision(root);
        int count = args[0] == "--checkpoint-capture"
            ? await GovernancePhaseWorkflow.RunWithDiskCheckpointsAsync(
                root, checkpointRevision, args[1])
            : await GovernancePhaseWorkflow.ResumeFromDiskCheckpointsAsync(
                args[1], checkpointRevision);
        Console.WriteLine(args[0] == "--checkpoint-capture"
            ? $"GOV_CHECKPOINTS_CAPTURED={count}; PHASE=OPEN"
            : $"GOV_CHECKPOINT_RESUMED_STEPS={count}; PHASE=OPEN");
        return count > 0 ? 0 : 2;
    }

    if (args.Length != 1 || args[0] is not
        ("--propose" or "--propose-workflow" or "--probe-workflow"))
    {
        Console.Error.WriteLine(
            "Usage: --check-profile | --propose | --propose-workflow | --probe-workflow");
        return 2;
    }

    // --probe-workflow only tests the deterministic handoff, without running
    // inference or pretending the generated text came from qwen3:4b.
    string issue = args[0] == "--probe-workflow"
        ? "Test-only synthetic proposal (NO MODEL INFERENCE)"
        : await Console.In.ReadToEndAsync();
    if (string.IsNullOrWhiteSpace(issue))
    {
        Console.Error.WriteLine("GOV_INPUT_MISSING: a nonempty issue is required on stdin.");
        return 2;
    }

    string proposal = args[0] == "--probe-workflow"
        ? issue
        : await GovernanceLocalProposalAgent.ProposeAsync(config, issue);

    if (args[0] == "--propose")
    {
        Console.WriteLine("UNVERIFIED_MODEL_PROPOSAL; NOT_ACCEPTANCE; NO_FILES_CHANGED");
        Console.WriteLine(proposal);
        return 0;
    }

    string sha = GetCleanRepositoryRevision(root);
    var handoff = new GovernancePhaseWorkflow.ProposalSubmission(
        proposal, sha, args[0] == "--probe-workflow"
            ? "test:synthetic-no-inference"
            : "ollama:qwen3:4b");
    var report = await GovernancePhaseWorkflow.RunAsync(
        root, sha, untrustedProposal: handoff);
    Console.WriteLine(JsonSerializer.Serialize(report,
        new JsonSerializerOptions { WriteIndented = true }));
    // 0 = diagnostic pipeline executed, NEVER automatic authorization.
    return report.Accepted ? 2 : 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine("GOV_LOCAL_MODEL_UNAVAILABLE: " + ex.GetType().Name + ": " + ex.Message);
    return 2;
}

static string FindRepositoryRoot()
{
    var directory = new DirectoryInfo(Directory.GetCurrentDirectory());
    while (directory is not null)
    {
        if (File.Exists(Path.Combine(directory.FullName,
                "infra/local-models/ollama-qwen3-4b.json")))
            return directory.FullName;
        directory = directory.Parent;
    }
    throw new InvalidOperationException("Run the CLI from within the PHANTOM repository.");
}

static string GetCleanRepositoryRevision(string root)
{
    static string Git(string root, string command)
    {
        using var process = new Process
        {
            StartInfo = new ProcessStartInfo("git")
            {
                WorkingDirectory = root,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false
            }
        };
        process.StartInfo.ArgumentList.Add(command);
        if (command == "rev-parse")
            process.StartInfo.ArgumentList.Add("HEAD");
        else if (command == "status")
            process.StartInfo.ArgumentList.Add("--porcelain");
        if (!process.Start())
            throw new InvalidOperationException("Unable to start Git.");
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        if (process.ExitCode != 0)
            throw new InvalidOperationException("GOV_GIT_UNAVAILABLE: " + stderr.Trim());
        return stdout.Trim();
    }

    if (!string.IsNullOrEmpty(Git(root, "status")))
        throw new InvalidOperationException(
            "GOV_UNCOMMITTED_SOURCE: proposals require a clean checkout at an immutable SHA.");
    string sha = Git(root, "rev-parse");
    if (sha.Length != 40 || !sha.All(Uri.IsHexDigit))
        throw new InvalidOperationException("GOV_REVISION_INVALID: expected full Git SHA-1 commit ID.");
    return sha;
}
