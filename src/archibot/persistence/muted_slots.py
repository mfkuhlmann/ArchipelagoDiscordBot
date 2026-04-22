"""muted_slots CRUD helpers."""
from __future__ import annotations

from archibot.persistence.db import Database


class MutedSlots:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def mute(self, channel_id: int, slot_name: str) -> None:
        await self.db.execute(
            """
            INSERT INTO muted_slots (channel_id, slot_name)
            VALUES (?, ?)
            ON CONFLICT(channel_id, slot_name) DO NOTHING
            """,
            (channel_id, slot_name),
        )

    async def unmute(self, channel_id: int, slot_name: str) -> int:
        row = await self.db.fetchone(
            "SELECT 1 FROM muted_slots WHERE channel_id = ? AND slot_name = ?",
            (channel_id, slot_name),
        )
        if row is None:
            return 0
        await self.db.execute(
            "DELETE FROM muted_slots WHERE channel_id = ? AND slot_name = ?",
            (channel_id, slot_name),
        )
        return 1

    async def is_muted(self, channel_id: int, slot_name: str) -> bool:
        row = await self.db.fetchone(
            "SELECT 1 FROM muted_slots WHERE channel_id = ? AND slot_name = ?",
            (channel_id, slot_name),
        )
        return row is not None

    async def list_for_channel(self, channel_id: int) -> list[str]:
        rows = await self.db.fetchall(
            "SELECT slot_name FROM muted_slots WHERE channel_id = ? ORDER BY slot_name",
            (channel_id,),
        )
        return [str(row["slot_name"]) for row in rows]
