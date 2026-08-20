function formatUser(user: { firstName: string; lastName: string }): string {
    const firstName = user.firstName;
    const lastName = user.lastName;
    return `${firstName} ${lastName}`;
}
