namespace Phantom.AgentFramework;

/// <summary>
/// Fail-closed Unix storage preflight. Host must also isolate untrusted processes
/// under different OS identities and deny direct access to the underlying store.
/// </summary>
public static class ResearchStorageBoundary
{
    public static void VerifyPrivateDirectory(string absoluteDirectory)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(absoluteDirectory);
        if (!Path.IsPathFullyQualified(absoluteDirectory))
            throw new ArgumentException("Storage directory must be absolute.", nameof(absoluteDirectory));
        if (!OperatingSystem.IsLinux() && !OperatingSystem.IsMacOS())
            throw new PlatformNotSupportedException("Unix permission verification required.");
        string directory = Path.GetFullPath(absoluteDirectory);
        if (!Directory.Exists(directory))
            throw new DirectoryNotFoundException(directory);
        var info = new DirectoryInfo(directory);
        if ((info.Attributes & FileAttributes.ReparsePoint) != 0)
            throw new UnauthorizedAccessException("Storage directory symlinks are forbidden.");
        UnixFileMode mode = File.GetUnixFileMode(directory);
        if ((mode & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite |
                     UnixFileMode.GroupExecute | UnixFileMode.OtherRead |
                     UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0)
            throw new UnauthorizedAccessException("Storage directory must be private to its owner.");
        foreach (string file in Directory.EnumerateFiles(directory))
        {
            var attributes = File.GetAttributes(file);
            if ((attributes & FileAttributes.ReparsePoint) != 0)
                throw new UnauthorizedAccessException("Storage symlinks are forbidden.");
            UnixFileMode fileMode = File.GetUnixFileMode(file);
            if ((fileMode & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite |
                             UnixFileMode.GroupExecute | UnixFileMode.OtherRead |
                             UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0)
                throw new UnauthorizedAccessException("Storage files must be private.");
        }
    }
}
