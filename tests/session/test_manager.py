import asyncio
from unittest.mock import AsyncMock

import pytest

from archibot.events import UnlockEvent
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.raspberry_counts import RaspberryCounts
from archibot.persistence.sessions import Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.manager import SessionManager


class FakeTrackerSession:
    def __init__(self, record, password, on_unlock, on_failure, on_state_change, on_room_info):
        self.record = record
        self.password = password
        self.on_unlock = on_unlock
        self.on_failure = on_failure
        self.on_state_change = on_state_change
        self.on_room_info = on_room_info
        self.state = "RUNNING"
        self.players = ["Meow", "Bork", "Zed"]

    def start(self):
        return asyncio.create_task(asyncio.sleep(0))

    async def stop(self):
        self.state = "DISCONNECTED"


@pytest.mark.asyncio
async def test_track_persists_and_creates_session(db):
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    assert manager.has_session(100)
    assert await manager.sessions.get(100) is not None
    await manager.close()


@pytest.mark.asyncio
async def test_consumer_coalesces_three_events(db):
    post_message = AsyncMock()
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=post_message,
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.slot_links.upsert(10, "Bork", 123)
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    event = UnlockEvent("Bork", "Meow", "Master Sword", "Eastern Palace", "A Link to the Past", 1)
    await manager._queue_unlock(100, event)
    await manager._queue_unlock(100, event)
    await manager._queue_unlock(100, event)
    await asyncio.sleep(2.2)
    assert post_message.await_count == 1
    sent_content = post_message.await_args.kwargs["content"]
    sent_embed = post_message.await_args.kwargs["embed"]
    assert "<@123>" in sent_content
    assert sent_embed.title == "3 unlocks"
    assert sent_embed.description.count("Master Sword") == 3
    await manager.close()


@pytest.mark.asyncio
async def test_consumer_sends_single_unlock_as_embed(db):
    post_message = AsyncMock()
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=post_message,
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.slot_links.upsert(10, "Bork", 123)
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    event = UnlockEvent("Bork", "Meow", "Master Sword", "Eastern Palace", "A Link to the Past", 1)
    await manager._queue_unlock(100, event)
    await asyncio.sleep(2.2)
    assert post_message.await_count == 1
    assert post_message.await_args.kwargs["content"] == "<@123>"
    assert post_message.await_args.kwargs["embed"].title == "🟣 Master Sword"
    await manager.close()


@pytest.mark.asyncio
async def test_restore_sessions_rehydrates_from_db(db):
    sessions = Sessions(db, PasswordCrypto(None))
    await sessions.upsert(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
        password="",
    )
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=sessions,
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.restore_sessions()
    assert manager.has_session(100)
    await manager.close()


@pytest.mark.asyncio
async def test_raspberry_counter_tracks_by_sender(db):
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    await manager._queue_unlock(100, UnlockEvent("Bork", "Meow", "Raspberry", "Loc 1", "Game", 0))
    await manager._queue_unlock(100, UnlockEvent("Zed", "Meow", "Raspberry", "Loc 2", "Game", 0))
    await manager._queue_unlock(100, UnlockEvent("Bork", "Bork", "Raspberry", "Loc 3", "Game", 0))
    await asyncio.sleep(2.2)
    total, counts = await manager.raspberry_summary(100)
    assert total == 3
    assert [(row.sender_slot, row.count) for row in counts] == [("Meow", 2), ("Bork", 1)]
    await manager.close()


@pytest.mark.asyncio
async def test_raspberry_counter_survives_untrack_for_same_room(db):
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    await manager._queue_unlock(100, UnlockEvent("Bork", "Meow", "Raspberry", "Loc 1", "Game", 0))
    await asyncio.sleep(2.2)
    await manager.untrack(100)
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    total, counts = await manager.raspberry_summary(100)
    assert total == 1
    assert [(row.sender_slot, row.count) for row in counts] == [("Meow", 1)]
    await manager.close()


@pytest.mark.asyncio
async def test_raspberry_counter_uses_room_seed_when_known(db):
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    session = manager._sessions[100]
    await session.on_room_info("Seed A")
    await manager._queue_unlock(100, UnlockEvent("Bork", "Meow", "Raspberry", "Loc 1", "Game", 0))
    await asyncio.sleep(2.2)
    await manager.untrack(100)
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    new_session = manager._sessions[100]
    await new_session.on_room_info("Seed B")
    total, counts = await manager.raspberry_summary(100)
    assert total == 0
    assert counts == []
    await manager.close()


@pytest.mark.asyncio
async def test_raspberry_counter_moves_host_port_count_to_seeded_room(db):
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
    )
    await manager._queue_unlock(100, UnlockEvent("Bork", "Meow", "Raspberry", "Loc 1", "Game", 0))
    await asyncio.sleep(2.2)
    session = manager._sessions[100]
    await session.on_room_info("Seed A")

    total, counts = await manager.raspberry_summary(100)
    assert total == 1
    assert [(row.sender_slot, row.count) for row in counts] == [("Meow", 1)]
    await manager.close()


@pytest.mark.asyncio
async def test_consumer_sends_single_unlock_as_plain_text_when_configured(db):
    post_message = AsyncMock()
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=post_message,
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.slot_links.upsert(10, "Bork", 123)
    await manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="plain",
    )
    event = UnlockEvent("Bork", "Meow", "Master Sword", "Eastern Palace", "A Link to the Past", 1)
    await manager._queue_unlock(100, event)
    await asyncio.sleep(2.2)
    assert post_message.await_count == 1
    assert "<@123>" in post_message.await_args.kwargs["content"]
    assert post_message.await_args.kwargs.get("embed") is None
    await manager.close()
