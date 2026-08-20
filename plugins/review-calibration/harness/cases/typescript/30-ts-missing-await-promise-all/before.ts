async function saveAll(items: Item[]): Promise<void> {
    await Promise.all(items.map(async (item) => {
        await repo.save(item);
    }));
}
