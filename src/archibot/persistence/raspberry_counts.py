"""Persistent hidden counter for Raspberry finds."""
from __future__ import annotations

from dataclasses import dataclass

from archibot.persistence.db import Database


@dataclass(frozen=True, slots=True)
class RaspberryCount:
    sender_slot: str
    count: int


class RaspberryCounts:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def increment(self, channel_id: int, sender_slot: str) -> None:
        row = await self.db.fetchone(
            """
            SELECT count FROM raspberry_counts
            WHERE channel_id = ? AND sender_slot = ?
            """,
            (channel_id, sender_slot),
        )
        if row is None:
            await self.db.execute(
                """
                INSERT INTO raspberry_counts (channel_id, sender_slot, count)
                VALUES (?, ?, 1)
                """,
                (channel_id, sender_slot),
            )
            return
        await self.db.execute(
            """
            UPDATE raspberry_counts
            SET count = count + 1
            WHERE channel_id = ? AND sender_slot = ?
            """,
            (channel_id, sender_slot),
        )

    async def summary_for_channel(self, channel_id: int) -> tuple[int, list[RaspberryCount]]:
        rows = await self.db.fetchall(
            """
            SELECT sender_slot, count
            FROM raspberry_counts
            WHERE channel_id = ?
            ORDER BY count DESC, sender_slot ASC
            """,
            (channel_id,),
        )
        counts = [
            RaspberryCount(sender_slot=str(row["sender_slot"]), count=int(row["count"]))
            for row in rows
        ]
        total = sum(row.count for row in counts)
        return total, counts

    async def clear_channel(self, channel_id: int) -> int:
        rows = await self.db.fetchall(
            "SELECT sender_slot FROM raspberry_counts WHERE channel_id = ?",
            (channel_id,),
        )
        if not rows:
            return 0
        await self.db.execute(
            "DELETE FROM raspberry_counts WHERE channel_id = ?",
            (channel_id,),
        )
        return len(rows)
