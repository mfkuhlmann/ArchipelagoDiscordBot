from archibot.persistence.raspberry_counts import RaspberryCounts


async def test_increment_and_summary(db):
    repo = RaspberryCounts(db)
    room_key = repo.room_key("localhost", 38281, "Sample Seed")
    await repo.increment(room_key, "Meow")
    await repo.increment(room_key, "Meow")
    await repo.increment(room_key, "Bork")
    total, counts = await repo.summary_for_room(room_key)
    assert total == 3
    assert [(row.sender_slot, row.count) for row in counts] == [("Meow", 2), ("Bork", 1)]


async def test_counts_are_separate_per_room(db):
    repo = RaspberryCounts(db)
    first_room = repo.room_key("localhost", 38281, "First Seed")
    second_room = repo.room_key("localhost", 38281, "Second Seed")
    await repo.increment(first_room, "Meow")
    await repo.increment(second_room, "Meow")
    await repo.increment(second_room, "Meow")

    first_total, first_counts = await repo.summary_for_room(first_room)
    second_total, second_counts = await repo.summary_for_room(second_room)

    assert first_total == 1
    assert [(row.sender_slot, row.count) for row in first_counts] == [("Meow", 1)]
    assert second_total == 2
    assert [(row.sender_slot, row.count) for row in second_counts] == [("Meow", 2)]


async def test_clear_room(db):
    repo = RaspberryCounts(db)
    room_key = repo.room_key("localhost", 38281, "Sample Seed")
    await repo.increment(room_key, "Meow")
    await repo.increment(room_key, "Bork")
    assert await repo.clear_room(room_key) == 2
    total, counts = await repo.summary_for_room(room_key)
    assert total == 0
    assert counts == []


async def test_merge_room_moves_counts(db):
    repo = RaspberryCounts(db)
    source_room = repo.room_key("localhost", 38281)
    target_room = repo.room_key("localhost", 38281, "Sample Seed")
    await repo.increment(source_room, "Meow")
    await repo.increment(source_room, "Meow")
    await repo.increment(target_room, "Bork")

    assert await repo.merge_room(source_room, target_room) == 1

    source_total, source_counts = await repo.summary_for_room(source_room)
    target_total, target_counts = await repo.summary_for_room(target_room)
    assert source_total == 0
    assert source_counts == []
    assert target_total == 3
    assert [(row.sender_slot, row.count) for row in target_counts] == [("Meow", 2), ("Bork", 1)]
