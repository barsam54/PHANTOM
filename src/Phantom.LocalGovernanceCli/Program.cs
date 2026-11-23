using Phantom.AgentFramework;

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

    if (args.Length != 1 || args[0] != "--propose")
    {
        Console.Error.WriteLine("Usage: --check-profile | --propose < issue-description.txt");
        return 2;
    }

    string issue = await Console.In.ReadToEndAsync();
    if (string.IsNullOrWhiteSpace(issue))
    {
        Console.Error.WriteLine("GOV_INPUT_MISSING: a nonempty issue is required on stdin.");
        return 2;
    }

    string proposal = await GovernanceLocalProposalAgent.ProposeAsync(config, issue);
    Console.WriteLine("UNVERIFIED_MODEL_PROPOSAL; NOT_ACCEPTANCE; NO_FILES_CHANGED");
    Console.WriteLine(proposal);
    return 0;
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
