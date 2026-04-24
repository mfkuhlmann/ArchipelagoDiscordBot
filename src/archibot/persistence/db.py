"""SQLite wrapper with schema creation."""
from __future__ import annotations

import aiosqlite

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS slot_links (
        guild_id        INTEGER NOT NULL,
        slot_name       TEXT    NOT NULL,
        discord_user_id INTEGER NOT NULL,
        created_at      TEXT    NOT NULL,
        PRIMARY KEY (guild_id, slot_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        channel_id      INTEGER PRIMARY KEY,
        guild_id        INTEGER NOT NULL,
        host            TEXT    NOT NULL,
        port            INTEGER NOT NULL,
        slot_name       TEXT    NOT NULL,
        message_style   TEXT    NOT NULL DEFAULT 'embed',
        room_seed_name  TEXT,
        password_enc    BLOB,
        created_at      TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS muted_slots (
        channel_id      INTEGER NOT NULL,
        slot_name       TEXT    NOT NULL,
        PRIMARY KEY (channel_id, slot_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS raspberry_counts (
        room_key        TEXT    NOT NULL,
        sender_slot     TEXT    NOT NULL,
        count           INTEGER NOT NULL,
        PRIMARY KEY (room_key, sender_slot)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """,
]


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.commit()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        return self._conn

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def execute(self, sql: str, params: tuple = ()) -> None:
        await self.conn.execute(sql, params)
        await self.conn.commit()

    async def fetchone(self, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
        async with self.conn.execute(sql, params) as cursor:
            return list(await cursor.fetchall())

    async def migrate(self) -> None:
        for statement in SCHEMA:
            await self.conn.execute(statement)
        await self._ensure_sessions_message_style_column()
        await self._ensure_sessions_room_seed_name_column()
        await self._ensure_raspberry_counts_room_key()
        row = await self.fetchone("SELECT version FROM schema_version")
        if row is None:
            await self.conn.execute("INSERT INTO schema_version (version) VALUES (1)")
        await self.conn.commit()

    async def _ensure_sessions_message_style_column(self) -> None:
        info = await self.fetchall("PRAGMA table_info(sessions)")
        columns = {row["name"] for row in info}
        if "message_style" in columns:
            return
        await self.conn.execute(
            "ALTER TABLE sessions ADD COLUMN message_style TEXT NOT NULL DEFAULT 'embed'"
        )

    async def _ensure_sessions_room_seed_name_column(self) -> None:
        info = await self.fetchall("PRAGMA table_info(sessions)")
        columns = {row["name"] for row in info}
        if "room_seed_name" in columns:
            return
        await self.conn.execute("ALTER TABLE sessions ADD COLUMN room_seed_name TEXT")

    async def _ensure_raspberry_counts_room_key(self) -> None:
        info = await self.fetchall("PRAGMA table_info(raspberry_counts)")
        columns = {row["name"] for row in info}
        if "room_key" in columns:
            return

        await self.conn.execute(
            """
            CREATE TABLE raspberry_counts_new (
                room_key        TEXT    NOT NULL,
                sender_slot     TEXT    NOT NULL,
                count           INTEGER NOT NULL,
                PRIMARY KEY (room_key, sender_slot)
            )
            """
        )
        await self.conn.execute(
            """
            INSERT INTO raspberry_counts_new (room_key, sender_slot, count)
            SELECT
                COALESCE('ap://' || sessions.host || ':' || sessions.port, 'channel:' || raspberry_counts.channel_id),
                raspberry_counts.sender_slot,
                SUM(raspberry_counts.count)
            FROM raspberry_counts
            LEFT JOIN sessions ON sessions.channel_id = raspberry_counts.channel_id
            GROUP BY
                COALESCE(
                    'ap://' || sessions.host || ':' || sessions.port,
                    'channel:' || raspberry_counts.channel_id
                ),
                raspberry_counts.sender_slot
            """
        )
        await self.conn.execute("DROP TABLE raspberry_counts")
        await self.conn.execute("ALTER TABLE raspberry_counts_new RENAME TO raspberry_counts")
