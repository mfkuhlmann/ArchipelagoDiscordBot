"""Session manager and message coalescing."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace

from archibot.events import UnlockEvent
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.raspberry_counts import RaspberryCount, RaspberryCounts
from archibot.persistence.sessions import SessionRecord, Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.formatter import (
    format_unlock,
    format_unlocks_batch,
    mention_for_user,
    unlock_embed,
)
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
        raspberry_counts: RaspberryCounts,
        password_crypto: PasswordCrypto,
        post_message: MessagePoster,
        post_failure: FailurePoster,
        session_factory: Callable[..., TrackerSession] = TrackerSession,
    ) -> None:
        self.slot_links = slot_links
        self.sessions = sessions
        self.muted_slots = muted_slots
        self.raspberry_counts = raspberry_counts
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

    async def raspberry_summary(self, channel_id: int) -> tuple[int, list[RaspberryCount]]:
        record = self._session_records.get(channel_id)
        if record is None:
            return 0, []
        return await self.raspberry_counts.summary_for_room(self._room_key(record))

    async def track(
        self,
        *,
        channel_id: int,
        guild_id: int,
        host: str,
        port: int,
        slot_name: str,
        message_style: str = "embed",
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
            message_style=message_style,
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
            on_room_info=lambda room_seed_name: self._set_room_seed_name(
                record.channel_id,
                room_seed_name,
            ),
        )
        self._sessions[record.channel_id] = session
        session.start()

    async def _set_room_seed_name(self, channel_id: int, room_seed_name: str) -> None:
        record = self._session_records.get(channel_id)
        if record is not None:
            updated_record = replace(record, room_seed_name=room_seed_name)
            await self.raspberry_counts.merge_room(
                self._room_key(record),
                self._room_key(updated_record),
            )
            self._session_records[channel_id] = updated_record
        await self.sessions.update_room_seed_name(channel_id, room_seed_name)

    def _room_key(self, record: SessionRecord) -> str:
        return self.raspberry_counts.room_key(record.host, record.port, record.room_seed_name)

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
                if queued_event.item_name.casefold() == "raspberry":
                    await self.raspberry_counts.increment(
                        self._room_key(self._session_records[channel_id]),
                        queued_event.sender_slot,
                    )
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

            if len(rendered) >= 3 and self._session_records[channel_id].message_style == "embed":
                content, embed = format_unlocks_batch(rendered)
                await self.post_message(channel_id=channel_id, content=content, embed=embed)
                continue

            for queued_event, user_id in rendered:
                if self._session_records[channel_id].message_style == "plain":
                    await self.post_message(
                        channel_id=channel_id,
                        content=format_unlock(queued_event, user_id),
                    )
                    continue
                await self.post_message(
                    channel_id=channel_id,
                    content=mention_for_user(user_id),
                    embed=unlock_embed(queued_event, user_id),
                )
