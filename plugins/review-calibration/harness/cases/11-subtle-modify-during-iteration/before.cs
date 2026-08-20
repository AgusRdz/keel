public void RemoveExpired(List<Session> sessions, DateTime now)
{
    var expired = sessions.Where(s => s.ExpiresAt < now).ToList();
    foreach (var s in expired)
    {
        sessions.Remove(s);
    }
}
