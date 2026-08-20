public decimal GetInvoiceTotal(IEnumerable<Line> lines, decimal taxRate)
{
    var subtotal = Subtotal(lines);
    return subtotal + subtotal * taxRate;
}

private static decimal Subtotal(IEnumerable<Line> lines)
{
    decimal sum = 0m;
    foreach (var line in lines)
    {
        sum += line.Quantity * line.UnitPrice;
    }
    return sum;
}
