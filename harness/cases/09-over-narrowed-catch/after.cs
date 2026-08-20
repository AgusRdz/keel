public bool TryDeleteCache(string path)
{
    try
    {
        File.Delete(path);
        return true;
    }
    catch (IOException)
    {
        // Cache file locked or already gone; best-effort cleanup, caller falls back.
        return false;
    }
}
