public bool TryDeleteCache(string path)
{
    try
    {
        File.Delete(path);
        return true;
    }
    catch (Exception)
    {
        return false;
    }
}
