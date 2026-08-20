public bool AnyOverdue(IEnumerable<Invoice> invoices, DateTime now)
{
    foreach (var invoice in invoices)
    {
        if (invoice.DueDate < now && !invoice.Paid)
        {
            return true;
        }
    }
    return false;
}
