function formatUser(user: { firstName: string; lastName: string }): string {
    const { firstName, lastName } = user;
    return `${firstName} ${lastName}`;
}
