using System.Net.Sockets;
using System.Runtime.Versioning;
using System.Text;
using System.Text.Json;

namespace Phantom.AgentFramework;

/// <summary>
/// Single-request-per-connection local grant server. Run only in a separate
/// trusted process with a private signing key and OS-managed socket permissions.
/// This class does not provision OS users or enforce cross-UID storage isolation.
/// </summary>
[SupportedOSPlatform("linux")]
public sealed class LinuxResearchGrantServer
{
    private readonly LinuxResearchGrantEndpoint endpoint;
    public LinuxResearchGrantServer(LinuxResearchGrantEndpoint endpoint) =>
        this.endpoint = endpoint ?? throw new ArgumentNullException(nameof(endpoint));

    public async Task ServeConnectionAsync(Socket accepted, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(accepted);
        using (accepted)
        {
            await using var stream = new NetworkStream(accepted, ownsSocket: false);
            using var reader = new StreamReader(stream, Encoding.UTF8, false, 1024, leaveOpen: true);
            await using var writer = new StreamWriter(stream, new UTF8Encoding(false), 1024, leaveOpen: true)
            { AutoFlush = true };
            try
            {
                // Bound requests; no unbounded JSON payloads or caller-supplied principals.
                char[] buffer = new char[4097];
                int count = 0;
                while (count < buffer.Length)
                {
                    int read = await reader.ReadAsync(buffer.AsMemory(count, 1), cancellationToken);
                    if (read == 0) break;
                    if (buffer[count++] == '\n') break;
                }
                if (count == 0 || count > 4096 || buffer[count - 1] != '\n')
                    throw new InvalidDataException("Request exceeds limit or is not newline terminated.");
                using JsonDocument json = JsonDocument.Parse(new string(buffer, 0, count));
                JsonElement root = json.RootElement;
                string experiment = root.GetProperty("experimentId").GetString()
                    ?? throw new InvalidDataException("Missing experiment ID.");
                DateTimeOffset cutoff = root.GetProperty("cutoffUtc").GetDateTimeOffset();
                string grant = endpoint.IssueForConnectedPeer(accepted, experiment, cutoff,
                    TimeSpan.FromMinutes(5));
                await writer.WriteLineAsync(JsonSerializer.Serialize(new { grant }));
            }
            catch (Exception ex) when (ex is UnauthorizedAccessException or JsonException or
                                       InvalidDataException or ArgumentException or KeyNotFoundException)
            {
                await writer.WriteLineAsync("{\"error\":\"denied\"}");
            }
        }
    }
}
