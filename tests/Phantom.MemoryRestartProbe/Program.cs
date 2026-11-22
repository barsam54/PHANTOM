using System.Security.Cryptography;
using System.Text;
using Phantom.AgentFramework;

if (args.Length != 2 || (args[0] != "write" && args[0] != "read" && args[0] != "stage-partial" && args[0] != "verify-partial"))
{
    Console.Error.WriteLine("Usage: write|read|stage-partial|verify-partial <absolute-external-directory>");
    return 2;
}

string root = Path.GetFullPath(args[1]);
if (!Path.IsPathFullyQualified(args[1]))
{
    Console.Error.WriteLine("Storage root must be absolute.");
    return 2;
}

string evidence = Path.Combine(root, "evidence.txt");
string memory = Path.Combine(root, "memory");
var observation = new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
var cutoff = observation.AddDays(1);
const string experimentId = "restart-probe-1";

try
{
    if (args[0] == "write")
    {
        Directory.CreateDirectory(root);
        string output = await FirstWorkflow.RunAsync("phantom");
        if (output != "MOTNAHP")
            throw new InvalidDataException("Unexpected workflow output.");
        byte[] bytes = Encoding.UTF8.GetBytes(output);
        await File.WriteAllBytesAsync(evidence, bytes);
        var candidate = new ResearchMemoryCandidate(
            experimentId, "restart-probe-v1", new Uri(evidence).AbsoluteUri,
            Convert.ToHexString(SHA256.HashData(bytes)),
            observation, cutoff, "train", true);
        await new ResearchMemoryStore(memory).SaveAsync(candidate);
        Console.WriteLine("WRITE_PASS");
    }
    else if (args[0] == "stage-partial")
    {
        Directory.CreateDirectory(memory);
        await File.WriteAllTextAsync(Path.Combine(memory, experimentId + ".json"), "{\\\"SchemaVersion\\\":1,");
        Console.WriteLine("PARTIAL_WRITE_READY");
        Console.Out.Flush();
        await Task.Delay(Timeout.InfiniteTimeSpan);
    }
    else if (args[0] == "verify-partial")
    {
        try
        {
            await new ResearchMemoryStore(memory).ReadAsync(experimentId);
            throw new InvalidOperationException("Corrupt manifest was accepted.");
        }
        catch (System.Text.Json.JsonException)
        {
            Console.WriteLine("CORRUPT_REJECTED");
        }
    }
    else
    {
        ResearchMemoryCandidate restored =
            await new ResearchMemoryStore(memory).ReadForAuthorizedExperimentAsync(
                experimentId, experimentId, cutoff);
        string output = await File.ReadAllTextAsync(new Uri(restored.EvidenceLocation).LocalPath);
        if (output != "MOTNAHP")
            throw new InvalidDataException("Restart output mismatch.");
        Console.WriteLine("RESTART_READ_PASS");
    }
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine($"{error.GetType().Name}: {error.Message}");
    return 1;
}
