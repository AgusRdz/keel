async function saveUser(user: User): Promise<void> {
    await repo.save(user);
    audit.log('user.saved', user.id);
}
