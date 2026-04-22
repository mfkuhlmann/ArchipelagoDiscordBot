import asyncio
from unittest.mock import AsyncMock

import pytest

from archibot.events import UnlockEvent
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.sessions import Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.manager import SessionManager


class FakeTrackerSession:
    def __init__(self, record, password, on_unlock, on_failure, on_state_change):
        self.record = record
        self.password = password
        self.on_unlock = on_unlock
        self.on_failure = on_failure
        self.on_state_change = on_state_change
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
    )
    event = UnlockEvent("Bork", "Meow", "Master Sword", "Eastern Palace", "A Link to the Past", 1)
    await manager._queue_unlock(100, event)
    await manager._queue_unlock(100, event)
    await manager._queue_unlock(100, event)
    await asyncio.sleep(2.2)
    assert post_message.await_count == 1
    sent = post_message.await_args.kwargs["content"]
    assert "<@123>" in sent
    assert sent.count("Master Sword") == 3
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
        password="",
    )
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=sessions,
        muted_slots=MutedSlots(db),
        password_crypto=PasswordCrypto(None),
        post_message=AsyncMock(),
        post_failure=AsyncMock(),
        session_factory=FakeTrackerSession,
    )
    await manager.restore_sessions()
    assert manager.has_session(100)
    await manager.close()
