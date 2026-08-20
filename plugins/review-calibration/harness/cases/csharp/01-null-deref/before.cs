public decimal GetOrderTotal(int orderId)
{
    var order = _orderRepository.Find(orderId);
    if (order == null)
    {
        return 0m;
    }
    return order.Lines.Sum(l => l.Amount);
}
