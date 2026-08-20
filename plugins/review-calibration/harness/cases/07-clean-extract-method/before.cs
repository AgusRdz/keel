public decimal GetInvoiceTotal(IEnumerable<Line> lines, decimal taxRate)
{
    decimal subtotal = 0m;
    foreach (var line in lines)
    {
        subtotal += line.Quantity * line.UnitPrice;
    }
    return subtotal + subtotal * taxRate;
}
