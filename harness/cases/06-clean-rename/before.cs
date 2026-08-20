public decimal ApplyDiscount(decimal amt, decimal rate)
{
    var discount = amt * rate;
    return amt - discount;
}
