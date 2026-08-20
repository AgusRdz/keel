public bool IsYes(string input)
{
    return input?.Trim().ToLowerInvariant() == "yes";
}
