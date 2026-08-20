public int SumFirst(int[] values, int count)
{
    var total = 0;
    for (var i = 0; i <= count; i++)
    {
        total += values[i];
    }
    return total;
}
