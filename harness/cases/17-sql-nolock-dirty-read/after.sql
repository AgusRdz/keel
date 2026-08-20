SELECT Balance
FROM Accounts WITH (NOLOCK)
WHERE AccountId = @accountId;
