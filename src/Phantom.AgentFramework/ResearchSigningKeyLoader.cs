using System.Runtime.Versioning;
using System.Security.Cryptography;

namespace Phantom.AgentFramework;

/// <summary>
/// Loads a host-provisioned signing key from an external file. Rotation requires
/// replacing the key and restarting the host; existing grants then fail closed.
/// </summary>
[SupportedOSPlatform("linux")]
[SupportedOSPlatform("macos")]
public static class ResearchSigningKeyLoader
{
    public static byte[] Load(string absolutePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(absolutePath);
        if (!Path.IsPathFullyQualified(absolutePath))
            throw new ArgumentException("Key path must be absolute.", nameof(absolutePath));
        string path = Path.GetFullPath(absolutePath);
        if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new UnauthorizedAccessException("Signing key symlinks are forbidden.");
        if (!OperatingSystem.IsLinux() && !OperatingSystem.IsMacOS())
            throw new PlatformNotSupportedException("Verified private key permissions require Unix.");

        UnixFileMode mode = File.GetUnixFileMode(path);
        if ((mode & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite |
                     UnixFileMode.GroupExecute | UnixFileMode.OtherRead |
                     UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0)
            throw new UnauthorizedAccessException("Signing key must not be accessible to group or others.");
        byte[] key = File.ReadAllBytes(path);
        if (key.Length != 32)
        {
            CryptographicOperations.ZeroMemory(key);
            throw new InvalidDataException("Signing key must be exactly 32 random bytes.");
        }
        return key;
    }
}
