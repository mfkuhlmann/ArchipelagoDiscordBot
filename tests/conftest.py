"""Shared pytest fixtures."""
from __future__ import annotations

import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.db import Database
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
        return None

    async def stop(self):
        self.state = "DISCONNECTED"


@pytest_asyncio.fixture
async def db() -> Database:
    database = Database(":memory:")
    await database.connect()
    await database.migrate()
    yield database
    await database.close()


def make_interaction(
    *,
    user_id: int = 42,
    guild_id: int = 10,
    channel_id: int = 100,
    is_mod: bool = True,
) -> SimpleNamespace:
    role_name = "AP-Mod" if is_mod else "Member"
    user = SimpleNamespace(
        id=user_id,
        roles=[SimpleNamespace(name=role_name)],
        guild_permissions=SimpleNamespace(manage_channels=False),
    )
    return SimpleNamespace(
        guild_id=guild_id,
        channel_id=channel_id,
        user=user,
        response=SimpleNamespace(send_message=AsyncMock()),
    )


@pytest_asyncio.fixture
async def cogs_setup(db: Database):
    post_message = AsyncMock()
    post_failure = AsyncMock()
    manager = SessionManager(
        slot_links=SlotLinks(db),
        sessions=Sessions(db, PasswordCrypto(None)),
        muted_slots=MutedSlots(db),
        raspberry_counts=RaspberryCounts(db),
        password_crypto=PasswordCrypto(None),
        post_message=post_message,
        post_failure=post_failure,
        session_factory=FakeTrackerSession,
    )
    bot = SimpleNamespace(
        config=SimpleNamespace(track_role_name="AP-Mod"),
        session_manager=manager,
    )
    yield bot, post_message, post_failure
    await manager.close()
