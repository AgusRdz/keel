public void TransferFunds(int from, int to, decimal amount)
{
    using var tx = _connection.BeginTransaction();
    _accounts.Debit(from, amount, tx);
    _accounts.Credit(to, amount, tx);
    tx.Commit();
}
