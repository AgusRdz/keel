public decimal GetOrderTotal(int orderId)
{
    var order = _orderRepository.Find(orderId);
    return order.Lines.Sum(l => l.Amount);
}
