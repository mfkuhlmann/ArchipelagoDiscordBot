"""Session manager and message coalescing."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from archibot.events import UnlockEvent
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.sessions import SessionRecord, Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.formatter import format_unlock, format_unlocks_batch
from archibot.session.tracker_session import TrackerSession

MessagePoster = Callable[..., Awaitable[None]]
FailurePoster = Callable[[int, SessionRecord, Exception, int], Awaitable[None]]


class SessionManager:
    """Coordinates tracker sessions and channel output."""

    def __init__(
        self,
        slot_links: SlotLinks,
        sessions: Sessions,
        muted_slots: MutedSlots,
        password_crypto: PasswordCrypto,
        post_message: MessagePoster,
        post_failure: FailurePoster,
        session_factory: Callable[..., TrackerSession] = TrackerSession,
    ) -> None:
        self.slot_links = slot_links
        self.sessions = sessions
        self.muted_slots = muted_slots
        self.password_crypto = password_crypto
        self.post_message = post_message
        self.post_failure = post_failure
        self.session_factory = session_factory
        self._sessions: dict[int, TrackerSession] = {}
        self._queues: dict[int, asyncio.Queue[UnlockEvent]] = {}
        self._consumers: dict[int, asyncio.Task[None]] = {}
        self._session_records: dict[int, SessionRecord] = {}

    async def restore_sessions(self) -> None:
        for record, password in await self.sessions.list_all():
            await self._start_session(record, password)

    async def close(self) -> None:
        for task in list(self._consumers.values()):
            task.cancel()
        for task in list(self._consumers.values()):
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._consumers.clear()
        for session in list(self._sessions.values()):
            await session.stop()
        self._sessions.clear()

    def has_session(self, channel_id: int) -> bool:
        return channel_id in self._sessions

    def state_for_channel(self, channel_id: int) -> str:
        session = self._sessions.get(channel_id)
        return "DISCONNECTED" if session is None else session.state

    def players_for_channel(self, channel_id: int) -> list[str]:
        session = self._sessions.get(channel_id)
        return [] if session is None else session.players

    async def track(
        self,
        *,
        channel_id: int,
        guild_id: int,
        host: str,
        port: int,
        slot_name: str,
        password: str = "",
    ) -> None:
        if channel_id in self._sessions:
            raise ValueError("This channel is already tracking a session")

        record = await self.sessions.upsert(
            channel_id=channel_id,
            guild_id=guild_id,
            host=host,
            port=port,
            slot_name=slot_name,
            password=password,
        )
        await self._start_session(record, password)

    async def untrack(self, channel_id: int) -> None:
        session = self._sessions.pop(channel_id, None)
        if session is not None:
            await session.stop()
        consumer = self._consumers.pop(channel_id, None)
        if consumer is not None:
            consumer.cancel()
            try:
                await consumer
            except asyncio.CancelledError:
                pass
        self._queues.pop(channel_id, None)
        self._session_records.pop(channel_id, None)
        await self.sessions.delete(channel_id)

    async def _start_session(self, record: SessionRecord, password: str) -> None:
        queue = self._queues.setdefault(record.channel_id, asyncio.Queue())
        self._session_records[record.channel_id] = record
        if record.channel_id not in self._consumers:
            self._consumers[record.channel_id] = asyncio.create_task(
                self._consume_channel(record.channel_id, record.guild_id, queue)
            )
        session = self.session_factory(
            record=record,
            password=password,
            on_unlock=lambda event: self._queue_unlock(record.channel_id, event),
            on_failure=lambda exc, attempts: self.post_failure(
                record.channel_id, record, exc, attempts
            ),
            on_state_change=lambda _state: asyncio.sleep(0),
        )
        self._sessions[record.channel_id] = session
        session.start()

    async def _queue_unlock(self, channel_id: int, event: UnlockEvent) -> None:
        await self._queues[channel_id].put(event)

    async def _consume_channel(
        self,
        channel_id: int,
        guild_id: int,
        queue: asyncio.Queue[UnlockEvent],
    ) -> None:
        while True:
            event = await queue.get()
            batch = [event]
            while True:
                try:
                    next_event = await asyncio.wait_for(queue.get(), timeout=2)
                except asyncio.TimeoutError:
                    break
                batch.append(next_event)

            rendered: list[tuple[UnlockEvent, int | None]] = []
            for queued_event in batch:
                if await self.muted_slots.is_muted(channel_id, queued_event.receiver_slot):
                    continue
                rendered.append(
                    (
                        queued_event,
                        await self.slot_links.get(guild_id, queued_event.receiver_slot),
                    )
                )

            if not rendered:
                continue

            if len(rendered) >= 3:
                await self.post_message(channel_id=channel_id, content=format_unlocks_batch(rendered))
                continue

            for queued_event, user_id in rendered:
                await self.post_message(
                    channel_id=channel_id,
                    content=format_unlock(queued_event, user_id),
                )
