from archibot.persistence.raspberry_counts import RaspberryCounts


async def test_increment_and_summary(db):
    repo = RaspberryCounts(db)
    await repo.increment(100, "Meow")
    await repo.increment(100, "Meow")
    await repo.increment(100, "Bork")
    total, counts = await repo.summary_for_channel(100)
    assert total == 3
    assert [(row.sender_slot, row.count) for row in counts] == [("Meow", 2), ("Bork", 1)]


async def test_clear_channel(db):
    repo = RaspberryCounts(db)
    await repo.increment(100, "Meow")
    await repo.increment(100, "Bork")
    assert await repo.clear_channel(100) == 2
    total, counts = await repo.summary_for_channel(100)
    assert total == 0
    assert counts == []
