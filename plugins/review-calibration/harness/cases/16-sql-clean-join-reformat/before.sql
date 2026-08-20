SELECT o.OrderId, o.Total, c.Name
FROM Orders o
INNER JOIN Customers c ON o.CustomerId = c.CustomerId
WHERE o.Status = 'Open';
