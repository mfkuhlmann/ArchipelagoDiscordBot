from archibot.persistence.slot_links import SlotLinks


async def test_add_and_get(db):
    repo = SlotLinks(db)
    await repo.upsert(10, "Meow", 42)
    assert await repo.get(10, "Meow") == 42


async def test_upsert_overwrites_existing(db):
    repo = SlotLinks(db)
    await repo.upsert(10, "Meow", 42)
    await repo.upsert(10, "Meow", 99)
    assert await repo.get(10, "Meow") == 99


async def test_remove_requires_owner(db):
    repo = SlotLinks(db)
    await repo.upsert(10, "Meow", 42)
    assert await repo.remove(10, "Meow", 99) == 0
    assert await repo.remove(10, "Meow", 42) == 1
    assert await repo.get(10, "Meow") is None


async def test_remove_all_for_user(db):
    repo = SlotLinks(db)
    await repo.upsert(10, "Meow", 42)
    await repo.upsert(10, "Bork", 42)
    assert await repo.remove_all_for_user(10, 42) == 2


async def test_list_by_guild(db):
    repo = SlotLinks(db)
    await repo.upsert(10, "Bork", 99)
    await repo.upsert(10, "Meow", 42)
    rows = await repo.list_by_guild(10)
    assert [row.slot_name for row in rows] == ["Bork", "Meow"]
