public async Task<string> LoadProfileAsync(int userId)
{
    var user = await _client.GetUserAsync(userId);
    return user.DisplayName;
}
