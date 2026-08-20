async function saveAll(items: Item[]): Promise<void> {
    Promise.all(items.map(async (item) => {
        await repo.save(item);
    }));
}
