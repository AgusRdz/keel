public string LoadProfile(int userId)
{
    var user = _client.GetUserAsync(userId).Result;
    return user.DisplayName;
}
