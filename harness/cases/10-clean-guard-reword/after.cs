public string FormatName(Customer customer)
{
    if (customer is null) return string.Empty;
    var full = $"{customer.First} {customer.Last}";
    return full.Trim();
}
