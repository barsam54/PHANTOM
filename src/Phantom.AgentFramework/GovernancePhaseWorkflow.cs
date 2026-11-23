using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Checkpointing;

namespace Phantom.AgentFramework;

/// <summary>
/// Executes the ten GOV-P0 preflight/verification decisions through the pinned
/// Microsoft Agent Framework runtime. This does NOT modify repository contents,
/// run a coding agent, certify scientific evidence, or restore external state.
/// </summary>
public static class GovernancePhaseWorkflow
{
    public static readonly string[] OrderedStages =
    [
        "discover", "baseline_review", "dependencies", "plan",
        "authorized_execute", "build_and_tests", "evidence",
        "acceptance", "publish", "checkpoint"
    ];

    public sealed record StepDecision(
        string Step, string Status, string Code, string Reason,
        string Action, string Evidence, string Resume);

    /// <summary>Untrusted model output is recorded by digest only and never grants authority.</summary>
    public sealed record ProposalSubmission(string Text, string BaseRevision, string Origin);

    public sealed record ProposalReceipt(string Sha256, string BaseRevision, string Origin);

    /// <summary>
    /// External CI evidence is input data, NOT self-authenticating approval.
    /// Runner and provider provenance must be verified independently.
    /// </summary>
    public sealed record EvidenceSubmission(
        string SchemaVersion, string Status, string SourceSha, string ContractSha256,
        string BaselineSha256, string ContractGate, string ReuseDecision,
        int CriteriaDiscovered, int HistoricalCiCriteriaVerified,
        int CurrentPhaseCriteriaVerified, bool PhaseEvidenceVerificationCompleted,
        string GovernanceAcceptance);

    public sealed record Report(
        string RepositoryRoot, string Revision, string Gate,
        string Acceptance, IReadOnlyList<StepDecision> Steps,
        ProposalReceipt? Proposal = null,
        EvidenceSubmission? EvidenceInput = null)
    {
        public bool Accepted => Acceptance == "PASS";
    }

    public static async Task<Report> RunAsync(
        string repositoryRoot, string revision, CancellationToken cancellationToken = default,
        ProposalSubmission? untrustedProposal = null,
        EvidenceSubmission? externalEvidence = null)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(repositoryRoot);
        ArgumentException.ThrowIfNullOrWhiteSpace(revision);
        if (!Path.IsPathFullyQualified(repositoryRoot))
            throw new ArgumentException("Repository root must be absolute.", nameof(repositoryRoot));
        if (!Directory.Exists(repositoryRoot))
            throw new DirectoryNotFoundException(repositoryRoot);
        cancellationToken.ThrowIfCancellationRequested();

        // One Microsoft Agent Framework workflow; no custom scheduling engine.
        // A caller-supplied proposal is never executable authority.
        // Keep only the hash/declared source in the workflow state and event stream.
        ProposalReceipt? receipt = null;
        if (untrustedProposal is not null)
        {
            if (string.IsNullOrWhiteSpace(untrustedProposal.Text) ||
                untrustedProposal.Text.Length > 16_000 ||
                string.IsNullOrWhiteSpace(untrustedProposal.Origin) ||
                untrustedProposal.Origin.Length > 100 ||
                string.IsNullOrWhiteSpace(untrustedProposal.BaseRevision))
                throw new ArgumentException(
                    "GOV_PROPOSAL_INVALID: proposal, origin and source revision are required and bounded.",
                    nameof(untrustedProposal));
            receipt = new ProposalReceipt(
                Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(untrustedProposal.Text))),
                untrustedProposal.BaseRevision, untrustedProposal.Origin);
        }
        Report start = new(repositoryRoot, revision, "GOV-P0", "OPEN",
            Array.Empty<StepDecision>(), receipt, externalEvidence);
        await using Run run = await InProcessExecution.RunAsync(BuildWorkflow(), start);
        cancellationToken.ThrowIfCancellationRequested();

        foreach (WorkflowEvent evt in run.NewEvents)
        {
            if (evt is ExecutorCompletedEvent done &&
                done.ExecutorId == "GovCheckpoint" && done.Data is Report report)
            {
                if (report.Steps.Count != OrderedStages.Length ||
                    !report.Steps.Select(x => x.Step).SequenceEqual(OrderedStages))
                    throw new InvalidOperationException("GOV_STAGE_ORDER_INVALID: ten-step chain incomplete.");
                if (report.Accepted)
                    throw new InvalidOperationException("GOV_FALSE_ACCEPTANCE: diagnostics cannot close GOV-P0.");
                return report;
            }
        }

        throw new InvalidOperationException("GOV_WORKFLOW_INCOMPLETE: final executor did not produce a report.");
    }

    /// <summary>
    /// Persists the same ten-stage read-only governance workflow using the official
    /// .NET filesystem JSON checkpoint store. Recovery does NOT restore external effects.
    /// </summary>
    public static async Task<int> RunWithDiskCheckpointsAsync(
        string repositoryRoot, string revision, string checkpointDirectory,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(repositoryRoot);
        ArgumentException.ThrowIfNullOrWhiteSpace(revision);
        ArgumentException.ThrowIfNullOrWhiteSpace(checkpointDirectory);
        if (!Path.IsPathFullyQualified(repositoryRoot) || !Directory.Exists(repositoryRoot))
            throw new ArgumentException("Repository root must exist and be absolute.", nameof(repositoryRoot));
        if (!Path.IsPathFullyQualified(checkpointDirectory))
            throw new ArgumentException("Checkpoint directory must be absolute.", nameof(checkpointDirectory));
        string projectPath = Path.GetFullPath(repositoryRoot) + Path.DirectorySeparatorChar;
        string checkpointPath = Path.GetFullPath(checkpointDirectory);
        if (checkpointPath.StartsWith(projectPath, StringComparison.Ordinal))
            throw new ArgumentException("Checkpoint data must remain outside the source tree.", nameof(checkpointDirectory));
        Directory.CreateDirectory(checkpointDirectory);
        cancellationToken.ThrowIfCancellationRequested();

        using var store = new FileSystemJsonCheckpointStore(new DirectoryInfo(checkpointDirectory));
        CheckpointManager manager = CheckpointManager.CreateJson(store);
        Report input = new(repositoryRoot, revision, "GOV-P0", "OPEN",
            Array.Empty<StepDecision>());
        await using StreamingRun run = await InProcessExecution.RunStreamingAsync(
            BuildWorkflow(), input, manager,
            sessionId: "gov-p0-" + revision, cancellationToken: cancellationToken);
        int outputs = 0;
        await foreach (WorkflowEvent evt in run.WatchStreamAsync(cancellationToken))
        {
            if (evt is WorkflowOutputEvent output && output.Data is Report report)
            {
                if (report.Acceptance != "OPEN" || report.Steps.Count != OrderedStages.Length)
                    throw new InvalidOperationException("GOV_CHECKPOINT_FALSE_ACCEPTANCE");
                outputs++;
            }
        }
        if (outputs != 1 || run.Checkpoints.Count == 0)
            throw new InvalidOperationException("GOV_CHECKPOINT_NOT_CAPTURED");
        return run.Checkpoints.Count;
    }

    /// <summary>Re-open a durable store and rehydrate the same Microsoft workflow.</summary>
    public static async Task<int> ResumeFromDiskCheckpointsAsync(
        string checkpointDirectory, string revision,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(checkpointDirectory);
        ArgumentException.ThrowIfNullOrWhiteSpace(revision);
        if (!Path.IsPathFullyQualified(checkpointDirectory) || !Directory.Exists(checkpointDirectory))
            throw new ArgumentException("Existing absolute checkpoint directory required.", nameof(checkpointDirectory));
        using var store = new FileSystemJsonCheckpointStore(new DirectoryInfo(checkpointDirectory));
        var index = (await store.RetrieveIndexAsync("gov-p0-" + revision)).ToArray();
        if (index.Length < 2)
            throw new InvalidOperationException("GOV_CHECKPOINT_HISTORY_MISSING");
        // Resume from the penultimate superstep to exercise actual work without repeating all
        // earlier steps. No external writes exist in this read-only governance workflow.
        CheckpointManager manager = CheckpointManager.CreateJson(store);
        await using Run run = await InProcessExecution.ResumeAsync(
            BuildWorkflow(), index[^2], manager, cancellationToken);
        cancellationToken.ThrowIfCancellationRequested();
        var reports = run.NewEvents.OfType<ExecutorCompletedEvent>()
            .Where(evt => evt.ExecutorId == "GovCheckpoint" && evt.Data is Report)
            .Select(evt => (Report)evt.Data!)
            .ToArray();
        if (reports.Length != 1 || reports[0].Acceptance != "OPEN" ||
            reports[0].Steps.Count != OrderedStages.Length)
            throw new InvalidOperationException("GOV_CHECKPOINT_RESUME_INCOMPLETE");
        return reports[0].Steps.Count;
    }

    private static Workflow BuildWorkflow()
    {
        // Ten stable executor identities are required by Microsoft checkpoint rehydration.
        var discover = ((Func<Report, Report>)Discover).BindAsExecutor("GovDiscover");
        var baseline = ((Func<Report, Report>)BaselineReview).BindAsExecutor("GovBaseline");
        var dependencies = ((Func<Report, Report>)Dependencies).BindAsExecutor("GovDependencies");
        var plan = ((Func<Report, Report>)Plan).BindAsExecutor("GovPlan");
        var execute = ((Func<Report, Report>)AuthorizedExecute).BindAsExecutor("GovExecute");
        var buildTests = ((Func<Report, Report>)BuildAndTests).BindAsExecutor("GovBuildTests");
        var evidence = ((Func<Report, Report>)Evidence).BindAsExecutor("GovEvidence");
        var acceptance = ((Func<Report, Report>)Acceptance).BindAsExecutor("GovAcceptance");
        var publish = ((Func<Report, Report>)Publish).BindAsExecutor("GovPublish");
        var checkpoint = ((Func<Report, Report>)Checkpoint).BindAsExecutor("GovCheckpoint");

        WorkflowBuilder builder = new(discover);
        builder.AddEdge(discover, baseline);
        builder.AddEdge(baseline, dependencies);
        builder.AddEdge(dependencies, plan);
        builder.AddEdge(plan, execute);
        builder.AddEdge(execute, buildTests);
        builder.AddEdge(buildTests, evidence);
        builder.AddEdge(evidence, acceptance);
        builder.AddEdge(acceptance, publish);
        builder.AddEdge(publish, checkpoint).WithOutputFrom(checkpoint);
        return builder.Build();

    }

    private static Report Add(Report report, string step, string status, string code,
        string reason, string action, string evidence, string resume) =>
        report with { Steps = [.. report.Steps,
            new StepDecision(step, status, code, reason, action, evidence, resume)] };

    private static string FileAt(Report report, string relative) =>
        Path.Combine(report.RepositoryRoot, relative.Replace('/', Path.DirectorySeparatorChar));

    private static Report Discover(Report state)
    {
        const string file = "docs/architecture/GOVERNANCE-CONTRACT.json";
        return File.Exists(FileAt(state, file))
            ? Add(state, "discover", "CHECK_OK", "GOV_CONTRACT_FOUND",
                "Versioned governance contract exists; content and historical evidence are not yet verified.",
                "Check the source revision and provenance for each stage.", file, "baseline_review")
            : Add(state, "discover", "BLOCKED", "GOV_CONTRACT_MISSING",
                "Governance contract does not exist in the selected revision.",
                "Restore the reviewed contract and rerun preflight.", file, "discover");
    }

    private static Report BaselineReview(Report state)
    {
        const string file = "docs/architecture/BASELINE.md";
        bool present = File.Exists(FileAt(state, file)) &&
            File.ReadAllText(FileAt(state, file), Encoding.UTF8)
                .Contains("Six simultaneous, complementary capabilities", StringComparison.Ordinal);
        return present
            ? Add(state, "baseline_review", "CHECK_OK", "GOV_BASELINE_FOUND",
                "Six-capability clause found; its scientific correctness is not assumed.",
                "Document and test any disputed clause before proposing an amendment.", file, "dependencies")
            : Add(state, "baseline_review", "BLOCKED", "GOV_BASELINE_MISSING",
                "Six-capability governance baseline clause is missing.",
                "Restore the approved clause or propose an evidenced correction.", file, "baseline_review");
    }

    private static Report Dependencies(Report state)
    {
        const string file = "src/Phantom.AgentFramework/Phantom.AgentFramework.csproj";
        bool declared = File.Exists(FileAt(state, file)) &&
            File.ReadAllText(FileAt(state, file), Encoding.UTF8)
                .Contains("Microsoft.Agents.AI.Workflows", StringComparison.Ordinal);
        return declared
            ? Add(state, "dependencies", "CHECK_OK", "GOV_FRAMEWORK_DECLARED",
                "Microsoft Agent Framework C# dependency declared; durable governance and worker dependencies remain unverified.",
                "Validate precise .NET API, worker permissions and checkpoint storage.", file, "plan")
            : Add(state, "dependencies", "BLOCKED", "GOV_FRAMEWORK_NOT_DECLARED",
                "No Microsoft Agent Framework C# workflow package reference found.",
                "Restore pinned official framework dependency and test build.", file, "dependencies");
    }

    private static Report Plan(Report state) =>
        Add(state, "plan", "CHECK_OK", "GOV_PLAN_TEMPLATE_FOUND",
            "Fixed stage order exists; an authorized change plan with prechange metrics has not executed.",
            "Create a stage-scoped plan with evidence, impact targets and rollback reference.",
            "docs/architecture/GOVERNANCE-CONTRACT.json", "authorized_execute");

    private static Report AuthorizedExecute(Report state)
    {
        if (state.Steps.Any(step => step.Status == "BLOCKED"))
            return Add(state, "authorized_execute", "SKIPPED", "GOV_UPSTREAM_BLOCKED",
                "A prerequisite was refused; no change may execute while it remains unresolved.",
                "Repair the first blocking prerequisite, rerun preflight and resume from the specified step.",
                "docs/architecture/GOVERNANCE-CONTRACT.json", "discover");

        if (!HasSourceFirstReview(state))
            return Add(state, "authorized_execute", "BLOCKED", "GOV_SOURCE_FIRST_REVIEW_MISSING",
                "The versioned official-source review record is missing, malformed or not reviewed.",
                "Review authoritative sources, compare reuse options and record the version-tested decision before any model proposal.",
                "docs/architecture/SOURCE-FIRST-DECISION.json", "baseline_review");

        if (state.Proposal is not null)
        {
            if (!string.Equals(state.Proposal.BaseRevision, state.Revision, StringComparison.Ordinal))
                return Add(state, "authorized_execute", "BLOCKED", "GOV_PROPOSAL_REVISION_MISMATCH",
                    "Untrusted model proposal refers to a different code revision.",
                    "Regenerate and review the proposal against the immutable current source revision.",
                    "sha256:" + state.Proposal.Sha256, "authorized_execute");
            return Add(state, "authorized_execute", "REVIEW_REQUIRED", "GOV_UNTRUSTED_PROPOSAL_RECORDED",
                "Model suggestion is recorded by digest, not validated, authorized or executed.",
                "Independently review sources, scope, risk, expected impact and recovery before any write-capable worker.",
                "sha256:" + state.Proposal.Sha256, "authorized_execute");
        }
        return Add(state, "authorized_execute", "NOT_IMPLEMENTED", "GOV_WORKER_UNAVAILABLE",
            "No independently qualified low-privilege coding worker is connected.",
            "Connect and test a bounded worker on an isolated branch before enabling modifications.",
            "docs/architecture/GOVERNANCE-CONTROLLER.md", "authorized_execute");
    }

    private static bool HasSourceFirstReview(Report state)
    {
        string file = FileAt(state, "docs/architecture/SOURCE-FIRST-DECISION.json");
        if (!File.Exists(file))
            return false;
        try
        {
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(file, Encoding.UTF8));
            JsonElement root = document.RootElement;
            if (!root.TryGetProperty("status", out var status) ||
                status.GetString() != "EVIDENCE_REVIEWED" ||
                !root.TryGetProperty("candidate_solutions", out var options) ||
                options.ValueKind != JsonValueKind.Array ||
                options.GetArrayLength() < 2 ||
                !root.TryGetProperty("official_sources", out var sources) ||
                sources.ValueKind != JsonValueKind.Array ||
                sources.GetArrayLength() < 1)
                return false;
            foreach (var item in sources.EnumerateArray())
            {
                if (!item.TryGetProperty("url", out var url) ||
                    !item.TryGetProperty("reviewed_version", out var version) ||
                    !item.TryGetProperty("verification", out var verification) ||
                    !Uri.TryCreate(url.GetString(), UriKind.Absolute, out Uri? parsed) ||
                    parsed.Scheme != Uri.UriSchemeHttps ||
                    parsed.Host is not ("learn.microsoft.com" or "docs.github.com" or "docs.ollama.com") ||
                    string.IsNullOrWhiteSpace(version.GetString()) ||
                    string.IsNullOrWhiteSpace(verification.GetString()))
                    return false;
            }
            // This read-only admission check is NOT authoritative verification of vendor
            // semantics; PR diff source coverage and CI are checked separately.
            return true;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException
            or JsonException or InvalidOperationException or ArgumentException)
        {
            return false;
        }
    }

    private static Report BuildAndTests(Report state) =>
        Add(state, "build_and_tests", "NOT_EXECUTED", "GOV_PHASE_TESTS_NOT_EXECUTED",
            "This governance workflow does not independently execute phase-specific .NET and impact tests.",
            "Use immutable SHA-based CI evidence plus matching pre/post measurements.",
            ".github/workflows/dotnet-build-test.yml", "build_and_tests");

    private static Report Evidence(Report state)
    {
        EvidenceSubmission? input = state.EvidenceInput;
        const string contract = "docs/architecture/GOVERNANCE-CONTRACT.json";
        if (input is null)
            return Add(state, "evidence", "BLOCKED", "GOV_EVIDENCE_INDEPENDENT_VERIFICATION_MISSING",
                "No verified CI evidence was provided to the governance workflow.",
                "Run the provider-backed independent validators for this exact source revision.",
                contract, "evidence");

        string baselineFile = FileAt(state, "docs/architecture/BASELINE.md");
        string contractFile = FileAt(state, contract);
        if (!File.Exists(baselineFile) || !File.Exists(contractFile) ||
            input.SchemaVersion != "phantom.governance.evidence-pipeline.v1" ||
            input.Status != "VERIFIED_SCOPE_ONLY" ||
            input.ContractGate != "GOV-P0" ||
            input.SourceSha != state.Revision ||
            input.ContractSha256 != Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(contractFile))).ToLowerInvariant() ||
            input.BaselineSha256 != Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselineFile))).ToLowerInvariant() ||
            input.CriteriaDiscovered != 6 ||
            input.HistoricalCiCriteriaVerified != 2 ||
            input.CurrentPhaseCriteriaVerified != 0 ||
            input.PhaseEvidenceVerificationCompleted ||
            input.GovernanceAcceptance != "OPEN" ||
            input.ReuseDecision is not ("BLOCKED" or "REUSABLE"))
            return Add(state, "evidence", "BLOCKED", "GOV_EVIDENCE_BINDING_INVALID",
                "The submitted evidence report does not match the exact checkout, baseline, contract or declared limited scope.",
                "Regenerate the independently validated report against this immutable revision; do not self-approve.",
                contract, "evidence");

        return Add(state, "evidence", "SCOPED_ONLY", "GOV_HISTORICAL_CI_RECEIPT_CONSUMED",
            "Two historical CI receipts were submitted with matching source/contract/baseline identifiers. This input is not standalone proof of provider authenticity or current phase acceptance.",
            "Continue with independently verified current-phase criteria, authorized execution and impact/rollback before acceptance.",
            contract, "evidence");
    }

    private static Report Acceptance(Report state) =>
        Add(state, "acceptance", "BLOCKED", "GOV_ACCEPTANCE_UNPROVEN",
            "The worker, impact, regression, rollback and acceptance proofs are absent.",
            "Keep P0 OPEN until independent positive and negative acceptance checks pass.",
            "docs/architecture/GOVERNANCE-CONTRACT.json", "acceptance");

    private static Report Publish(Report state) =>
        Add(state, "publish", "NOT_IMPLEMENTED", "GOV_PUBLICATION_NOT_VERIFIED",
            "Stage-specific automated evidence PR and GitHub Projects update are not operational.",
            "Implement idempotent least-privilege publication and verify dashboard consistency.",
            ".github/workflows/repository-policy.yml", "publish");

    private static Report Checkpoint(Report state) =>
        Add(state, "checkpoint", "NOT_IMPLEMENTED", "GOV_DURABLE_RESUME_NOT_VERIFIED",
            "No governance checkpoint across process restart or recovery of external effects exists.",
            "Add approved persistent checkpoint storage, idempotent side effects and forced-restart tests.",
            "docs/architecture/GOVERNANCE-CONTROLLER.md", "checkpoint");
}
