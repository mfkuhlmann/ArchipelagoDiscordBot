"""slot_links CRUD helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from archibot.persistence.db import Database


@dataclass(frozen=True, slots=True)
class SlotLink:
    guild_id: int
    slot_name: str
    discord_user_id: int
    created_at: str


class SlotLinks:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert(self, guild_id: int, slot_name: str, discord_user_id: int) -> None:
        await self.db.execute(
            """
            INSERT INTO slot_links (guild_id, slot_name, discord_user_id, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, slot_name) DO UPDATE
            SET discord_user_id = excluded.discord_user_id
            """,
            (guild_id, slot_name, discord_user_id, datetime.now(UTC).isoformat()),
        )

    async def get(self, guild_id: int, slot_name: str) -> int | None:
        row = await self.db.fetchone(
            "SELECT discord_user_id FROM slot_links WHERE guild_id = ? AND slot_name = ?",
            (guild_id, slot_name),
        )
        return None if row is None else int(row["discord_user_id"])

    async def remove(self, guild_id: int, slot_name: str, discord_user_id: int) -> int:
        before = await self.db.fetchone(
            """
            SELECT 1 FROM slot_links
            WHERE guild_id = ? AND slot_name = ? AND discord_user_id = ?
            """,
            (guild_id, slot_name, discord_user_id),
        )
        if before is None:
            return 0
        await self.db.execute(
            """
            DELETE FROM slot_links
            WHERE guild_id = ? AND slot_name = ? AND discord_user_id = ?
            """,
            (guild_id, slot_name, discord_user_id),
        )
        return 1

    async def remove_all_for_user(self, guild_id: int, discord_user_id: int) -> int:
        rows = await self.db.fetchall(
            "SELECT slot_name FROM slot_links WHERE guild_id = ? AND discord_user_id = ?",
            (guild_id, discord_user_id),
        )
        await self.db.execute(
            "DELETE FROM slot_links WHERE guild_id = ? AND discord_user_id = ?",
            (guild_id, discord_user_id),
        )
        return len(rows)

    async def list_by_guild(self, guild_id: int) -> list[SlotLink]:
        rows = await self.db.fetchall(
            """
            SELECT guild_id, slot_name, discord_user_id, created_at
            FROM slot_links
            WHERE guild_id = ?
            ORDER BY slot_name
            """,
            (guild_id,),
        )
        return [
            SlotLink(
                guild_id=int(row["guild_id"]),
                slot_name=str(row["slot_name"]),
                discord_user_id=int(row["discord_user_id"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]
