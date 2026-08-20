SELECT o.OrderId, o.Total, c.Name
FROM Orders AS o
JOIN Customers AS c ON o.CustomerId = c.CustomerId
WHERE o.Status = 'Open';
