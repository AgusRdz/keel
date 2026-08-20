public User FindByEmail(string email)
{
    using var cmd = _connection.CreateCommand();
    cmd.CommandText = "SELECT * FROM Users WHERE Email = @email";
    cmd.Parameters.AddWithValue("@email", email);
    return Map(cmd.ExecuteReader());
}
