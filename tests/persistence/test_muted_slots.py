from archibot.persistence.muted_slots import MutedSlots


async def test_mute_and_is_muted(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Meow")
    assert await repo.is_muted(100, "Meow")


async def test_unmute(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Meow")
    assert await repo.unmute(100, "Meow") == 1
    assert not await repo.is_muted(100, "Meow")


async def test_list_for_channel(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Bork")
    await repo.mute(100, "Meow")
    assert await repo.list_for_channel(100) == ["Bork", "Meow"]
