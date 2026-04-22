"""sessions CRUD helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.db import Database


@dataclass(frozen=True, slots=True)
class SessionRecord:
    channel_id: int
    guild_id: int
    host: str
    port: int
    slot_name: str
    created_at: str


class Sessions:
    def __init__(self, db: Database, crypto: PasswordCrypto) -> None:
        self.db = db
        self.crypto = crypto

    async def upsert(
        self,
        *,
        channel_id: int,
        guild_id: int,
        host: str,
        port: int,
        slot_name: str,
        password: str,
    ) -> SessionRecord:
        created_at = datetime.now(UTC).isoformat()
        password_enc = self.crypto.encrypt(password)
        await self.db.execute(
            """
            INSERT INTO sessions (
                channel_id, guild_id, host, port, slot_name, password_enc, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE
            SET guild_id = excluded.guild_id,
                host = excluded.host,
                port = excluded.port,
                slot_name = excluded.slot_name,
                password_enc = excluded.password_enc
            """,
            (channel_id, guild_id, host, port, slot_name, password_enc, created_at),
        )
        return SessionRecord(channel_id, guild_id, host, port, slot_name, created_at)

    async def get(self, channel_id: int) -> tuple[SessionRecord, str] | None:
        row = await self.db.fetchone(
            """
            SELECT channel_id, guild_id, host, port, slot_name, password_enc, created_at
            FROM sessions
            WHERE channel_id = ?
            """,
            (channel_id,),
        )
        if row is None:
            return None
        return self._row_to_record(row)

    async def list_all(self) -> list[tuple[SessionRecord, str]]:
        rows = await self.db.fetchall(
            """
            SELECT channel_id, guild_id, host, port, slot_name, password_enc, created_at
            FROM sessions
            ORDER BY channel_id
            """
        )
        return [self._row_to_record(row) for row in rows]

    async def delete(self, channel_id: int) -> int:
        exists = await self.db.fetchone(
            "SELECT channel_id FROM sessions WHERE channel_id = ?",
            (channel_id,),
        )
        if exists is None:
            return 0
        await self.db.execute("DELETE FROM sessions WHERE channel_id = ?", (channel_id,))
        return 1

    def _row_to_record(self, row) -> tuple[SessionRecord, str]:
        return (
            SessionRecord(
                channel_id=int(row["channel_id"]),
                guild_id=int(row["guild_id"]),
                host=str(row["host"]),
                port=int(row["port"]),
                slot_name=str(row["slot_name"]),
                created_at=str(row["created_at"]),
            ),
            self.crypto.decrypt(row["password_enc"]),
        )
