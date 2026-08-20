public string FormatName(Customer customer)
{
    if (customer == null) return string.Empty;
    return $"{customer.First} {customer.Last}".Trim();
}
