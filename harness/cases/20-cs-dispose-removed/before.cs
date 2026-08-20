public string ReadAllText(string path)
{
    using var reader = new StreamReader(path);
    return reader.ReadToEnd();
}
