public void RemoveExpired(List<Session> sessions, DateTime now)
{
    foreach (var s in sessions)
    {
        if (s.ExpiresAt < now)
        {
            sessions.Remove(s);
        }
    }
}
