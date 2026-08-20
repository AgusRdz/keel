public string Classify(int score)
{
    string result;
    if (score >= 90)
    {
        result = "A";
    }
    else if (score >= 80)
    {
        result = "B";
    }
    else
    {
        result = "C";
    }
    return result;
}
