import asyncio
import socket
from unittest.mock import AsyncMock

import pytest

from archibot.archipelago.protocol import ArchipelagoConnectionRefused
from archibot.events import UnlockEvent
from archibot.persistence.sessions import SessionRecord
from archibot.session.tracker_session import TrackerSession


class SuccessfulClient:
    def __init__(self, *_args, on_unlock=None, **_kwargs):
        self.on_unlock = on_unlock
        self.players = ["Meow", "Bork"]

    async def run(self, _password=""):
        if self.on_unlock is not None:
            await self.on_unlock(
                UnlockEvent("Bork", "Meow", "Master Sword", "Eastern Palace", "A Link to the Past", 1)
            )
        return

    async def close(self):
        return None


class RefusedClient:
    def __init__(self, *_args, **_kwargs):
        self.players = []

    async def run(self, _password=""):
        raise ArchipelagoConnectionRefused(["InvalidSlot"])

    async def close(self):
        return None


def record() -> SessionRecord:
    return SessionRecord(100, 10, "localhost", 38281, "Meow", "now")


@pytest.mark.asyncio
async def test_tracker_session_reports_unlock_and_disconnects():
    on_unlock = AsyncMock()
    on_failure = AsyncMock()
    session = TrackerSession(
        record=record(),
        password="",
        on_unlock=on_unlock,
        on_failure=on_failure,
        client_factory=SuccessfulClient,
    )
    task = session.start()
    await asyncio.sleep(0.05)
    await session.stop()
    assert on_unlock.await_count == 1
    assert task.done()


@pytest.mark.asyncio
async def test_tracker_session_stops_on_non_retryable_failure():
    on_unlock = AsyncMock()
    on_failure = AsyncMock()
    session = TrackerSession(
        record=record(),
        password="",
        on_unlock=on_unlock,
        on_failure=on_failure,
        client_factory=RefusedClient,
    )
    session.start()
    await asyncio.sleep(0.05)
    assert session.state == "DISCONNECTED"
    assert on_failure.await_count == 1


def test_dns_error_is_non_retryable():
    session = TrackerSession(record(), "", AsyncMock(), AsyncMock())
    assert session._is_non_retryable(socket.gaierror("dns"))
