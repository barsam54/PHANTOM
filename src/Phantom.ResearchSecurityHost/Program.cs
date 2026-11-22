using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using Phantom.AgentFramework;

[assembly: SupportedOSPlatform("linux")]

if (!OperatingSystem.IsLinux())
    throw new PlatformNotSupportedException("Linux required.");
if (args.Length != 6 ||
    !uint.TryParse(args[4], out uint workerUid) ||
    !DateTimeOffset.TryParseExact(args[5], "O", System.Globalization.CultureInfo.InvariantCulture,
        System.Globalization.DateTimeStyles.None, out DateTimeOffset cutoff) ||
    cutoff.Offset != TimeSpan.Zero)
    throw new ArgumentException("Usage: host <socket-directory> <memory-directory> <key-file> <experiment-id> <worker-uid> <maximum-cutoff-utc-O>");

string socketDirectory = Path.GetFullPath(args[0]);
string memoryDirectory = Path.GetFullPath(args[1]);
string keyPath = Path.GetFullPath(args[2]);
string experimentId = args[3];
if (!Path.IsPathFullyQualified(args[0]) || !Path.IsPathFullyQualified(args[1]) ||
    !Path.IsPathFullyQualified(args[2]) || string.IsNullOrWhiteSpace(experimentId))
    throw new ArgumentException("Absolute paths and nonempty experiment ID required.");
if (GetUid() == workerUid)
    throw new UnauthorizedAccessException("Worker and trusted host must have distinct Linux UIDs.");
ResearchStorageBoundary.VerifyPrivateDirectory(memoryDirectory);
if ((File.GetAttributes(socketDirectory) & FileAttributes.ReparsePoint) != 0)
    throw new UnauthorizedAccessException("Socket directory symlinks forbidden.");
UnixFileMode socketMode = File.GetUnixFileMode(socketDirectory);
if (socketMode != (UnixFileMode.UserRead | UnixFileMode.UserWrite |
                   UnixFileMode.UserExecute | UnixFileMode.GroupExecute))
    throw new UnauthorizedAccessException("Socket directory must have mode 0710.");
string keyDirectory = Path.GetDirectoryName(keyPath)
    ?? throw new UnauthorizedAccessException("Invalid key directory.");
ResearchStorageBoundary.VerifyPrivateDirectory(keyDirectory);
string socketPath = Path.Combine(socketDirectory, "research.sock");
if (File.Exists(socketPath))
    throw new IOException("Socket path already exists; refusing to replace it.");
byte[] key = ResearchSigningKeyLoader.Load(keyPath);
SignedResearchMemoryAccess signer;
try
{
    signer = new SignedResearchMemoryAccess(new ResearchMemoryStore(memoryDirectory), key);
}
finally
{
    CryptographicOperations.ZeroMemory(key);
}
var handler = new LinuxResearchGrantServer(new LinuxResearchGrantEndpoint(
    new LinuxPeerIdentityProvider(new Dictionary<uint, string> { [workerUid] = experimentId }, cutoff),
    new TrustedResearchGrantIssuer(signer)), signer);
using var listener = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
listener.Bind(new UnixDomainSocketEndPoint(socketPath));
try
{
    // A separate trusted administrator must configure socket directory traversal
    // and socket group ownership for the authorized worker UID.
    File.SetUnixFileMode(socketPath, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.GroupRead | UnixFileMode.GroupWrite);
    listener.Listen(16);
    using var shutdown = new CancellationTokenSource();
    Console.CancelKeyPress += (_, e) => { e.Cancel = true; shutdown.Cancel(); };
    while (!shutdown.IsCancellationRequested)
    {
        Socket peer;
        try { peer = await listener.AcceptAsync(shutdown.Token); }
        catch (OperationCanceledException) { break; }
        // Handle sequentially to cap concurrency and prevent unbounded worker load.
        await handler.ServeConnectionAsync(peer, shutdown.Token);
    }
}
finally
{
    listener.Dispose();
    if (File.Exists(socketPath)) File.Delete(socketPath);
}

[DllImport("libc", EntryPoint = "getuid")]
static extern uint GetUid();
