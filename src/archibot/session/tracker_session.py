"""Session lifecycle and retry handling."""
from __future__ import annotations

import asyncio
import socket
import time
from collections.abc import Awaitable, Callable

import websockets

from archibot.archipelago.client import ArchipelagoClient
from archibot.archipelago.protocol import ArchipelagoConnectionRefused
from archibot.events import UnlockEvent
from archibot.persistence.sessions import SessionRecord

BACKOFF_SCHEDULE = [1, 2, 4, 8, 16, 32, 60]
MAX_TRANSIENT_RETRY_SECONDS = 60 * 60
NON_RETRYABLE_ERRORS = {"InvalidSlot", "InvalidGame", "InvalidPassword"}

UnlockHandler = Callable[[UnlockEvent], Awaitable[None]]
FailureHandler = Callable[[Exception, int], Awaitable[None]]
StateHandler = Callable[[str], Awaitable[None]]
RoomInfoHandler = Callable[[str], Awaitable[None]]


class TrackerSession:
    """Owns one AP WebSocket session with bounded transient retries."""

    def __init__(
        self,
        record: SessionRecord,
        password: str,
        on_unlock: UnlockHandler,
        on_failure: FailureHandler,
        on_state_change: StateHandler | None = None,
        on_room_info: RoomInfoHandler | None = None,
        client_factory: Callable[..., ArchipelagoClient] = ArchipelagoClient,
    ) -> None:
        self.record = record
        self.password = password
        self.on_unlock = on_unlock
        self.on_failure = on_failure
        self.on_state_change = on_state_change
        self.on_room_info = on_room_info
        self.client_factory = client_factory
        self.state = "DISCONNECTED"
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._client: ArchipelagoClient | None = None

    def start(self) -> asyncio.Task[None]:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name=f"tracker-{self.record.channel_id}")
        return self._task

    async def stop(self) -> None:
        self._stop_event.set()
        if self._client is not None:
            await self._client.close()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._set_state("DISCONNECTED")

    @property
    def players(self) -> list[str]:
        if self._client is None:
            return []
        return self._client.players

    async def _set_state(self, state: str) -> None:
        self.state = state
        if self.on_state_change is not None:
            await self.on_state_change(state)

    async def _run(self) -> None:
        attempts = 0
        stable_since: float | None = None
        retry_started_at: float | None = None
        while not self._stop_event.is_set():
            next_state = "RECONNECTING" if attempts else "CONNECTING"
            await self._set_state(next_state)
            try:
                self._client = self.client_factory(
                    self.record.host,
                    self.record.port,
                    self.record.slot_name,
                    on_unlock=self.on_unlock,
                    on_room_info=self.on_room_info,
                )
                await self._set_state("RUNNING")
                stable_since = time.monotonic()
                await self._client.run(self.password)
                if self._stop_event.is_set():
                    break
                raise websockets.ConnectionClosed(None, None)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                now = time.monotonic()
                if stable_since is not None and now - stable_since >= 60:
                    attempts = 0
                    retry_started_at = None
                stable_since = None
                if self._is_non_retryable(exc):
                    await self._set_state("DISCONNECTED")
                    await self.on_failure(exc, attempts if attempts else 1)
                    return
                if retry_started_at is None:
                    retry_started_at = now
                retry_elapsed = now - retry_started_at
                if retry_elapsed >= MAX_TRANSIENT_RETRY_SECONDS:
                    await self._set_state("DISCONNECTED")
                    await self.on_failure(exc, attempts if attempts else 1)
                    return
                delay = BACKOFF_SCHEDULE[min(attempts, len(BACKOFF_SCHEDULE) - 1)]
                delay = min(delay, MAX_TRANSIENT_RETRY_SECONDS - retry_elapsed)
                attempts += 1
                await self._set_state("RECONNECTING")
                await asyncio.sleep(delay)
        await self._set_state("DISCONNECTED")

    def _is_non_retryable(self, exc: Exception) -> bool:
        if isinstance(exc, ArchipelagoConnectionRefused):
            return any(error in NON_RETRYABLE_ERRORS for error in exc.errors)
        return isinstance(exc, socket.gaierror)
