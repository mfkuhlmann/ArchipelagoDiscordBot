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

    @staticmethod
    def room_key(host: str, port: int, room_seed_name: str | None = None) -> str:
        base = f"ap://{host}:{port}"
        if room_seed_name is None:
            return base
        return f"{base}/{room_seed_name}"

    async def increment(self, room_key: str, sender_slot: str) -> None:
        row = await self.db.fetchone(
            """
            SELECT count FROM raspberry_counts
            WHERE room_key = ? AND sender_slot = ?
            """,
            (room_key, sender_slot),
        )
        if row is None:
            await self.db.execute(
                """
                INSERT INTO raspberry_counts (room_key, sender_slot, count)
                VALUES (?, ?, 1)
                """,
                (room_key, sender_slot),
            )
            return
        await self.db.execute(
            """
            UPDATE raspberry_counts
            SET count = count + 1
            WHERE room_key = ? AND sender_slot = ?
            """,
            (room_key, sender_slot),
        )

    async def summary_for_room(self, room_key: str) -> tuple[int, list[RaspberryCount]]:
        rows = await self.db.fetchall(
            """
            SELECT sender_slot, count
            FROM raspberry_counts
            WHERE room_key = ?
            ORDER BY count DESC, sender_slot ASC
            """,
            (room_key,),
        )
        counts = [
            RaspberryCount(sender_slot=str(row["sender_slot"]), count=int(row["count"]))
            for row in rows
        ]
        total = sum(row.count for row in counts)
        return total, counts

    async def merge_room(self, source_room_key: str, target_room_key: str) -> int:
        if source_room_key == target_room_key:
            return 0
        rows = await self.db.fetchall(
            """
            SELECT sender_slot, count
            FROM raspberry_counts
            WHERE room_key = ?
            """,
            (source_room_key,),
        )
        for row in rows:
            await self.db.execute(
                """
                INSERT INTO raspberry_counts (room_key, sender_slot, count)
                VALUES (?, ?, ?)
                ON CONFLICT(room_key, sender_slot) DO UPDATE
                SET count = count + excluded.count
                """,
                (target_room_key, row["sender_slot"], row["count"]),
            )
        if rows:
            await self.db.execute(
                "DELETE FROM raspberry_counts WHERE room_key = ?",
                (source_room_key,),
            )
        return len(rows)

    async def clear_room(self, room_key: str) -> int:
        rows = await self.db.fetchall(
            "SELECT sender_slot FROM raspberry_counts WHERE room_key = ?",
            (room_key,),
        )
        if not rows:
            return 0
        await self.db.execute(
            "DELETE FROM raspberry_counts WHERE room_key = ?",
            (room_key,),
        )
        return len(rows)
