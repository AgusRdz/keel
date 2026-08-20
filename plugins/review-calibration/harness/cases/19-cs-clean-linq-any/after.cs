public bool AnyOverdue(IEnumerable<Invoice> invoices, DateTime now)
{
    return invoices.Any(invoice => invoice.DueDate < now && !invoice.Paid);
}
