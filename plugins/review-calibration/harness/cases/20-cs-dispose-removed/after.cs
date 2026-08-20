public string ReadAllText(string path)
{
    var reader = new StreamReader(path);
    return reader.ReadToEnd();
}
