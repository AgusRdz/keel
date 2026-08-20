public decimal ApplyDiscount(decimal amount, decimal rate)
{
    var discount = amount * rate;
    return amount - discount;
}
