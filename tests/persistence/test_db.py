from archibot.persistence.db import Database


async def test_migrate_creates_all_tables(db):
    tables = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    names = {row["name"] for row in tables}
    assert {
        "slot_links",
        "sessions",
        "muted_slots",
        "raspberry_counts",
        "schema_version",
    }.issubset(names)


async def test_migrate_is_idempotent(db):
    await db.migrate()
    await db.migrate()
    version = await db.fetchone("SELECT version FROM schema_version")
    assert version["version"] >= 1


async def test_slot_links_columns(db):
    info = await db.fetchall("PRAGMA table_info(slot_links)")
    cols = {row["name"] for row in info}
    assert cols == {"guild_id", "slot_name", "discord_user_id", "created_at"}


async def test_sessions_columns(db):
    info = await db.fetchall("PRAGMA table_info(sessions)")
    cols = {row["name"] for row in info}
    assert cols == {
        "channel_id",
        "guild_id",
        "host",
        "port",
        "slot_name",
        "message_style",
        "room_seed_name",
        "password_enc",
        "created_at",
    }


async def test_muted_slots_columns(db):
    info = await db.fetchall("PRAGMA table_info(muted_slots)")
    cols = {row["name"] for row in info}
    assert cols == {"channel_id", "slot_name"}


async def test_raspberry_counts_columns(db):
    info = await db.fetchall("PRAGMA table_info(raspberry_counts)")
    cols = {row["name"] for row in info}
    assert cols == {"room_key", "sender_slot", "count"}


async def test_migrate_converts_channel_raspberry_counts_to_room_keys():
    database = Database(":memory:")
    await database.connect()
    try:
        await database.conn.execute(
            """
            CREATE TABLE sessions (
                channel_id      INTEGER PRIMARY KEY,
                guild_id        INTEGER NOT NULL,
                host            TEXT    NOT NULL,
                port            INTEGER NOT NULL,
                slot_name       TEXT    NOT NULL,
                message_style   TEXT    NOT NULL DEFAULT 'embed',
                password_enc    BLOB,
                created_at      TEXT    NOT NULL
            )
            """
        )
        await database.conn.execute(
            """
            CREATE TABLE raspberry_counts (
                channel_id      INTEGER NOT NULL,
                sender_slot     TEXT    NOT NULL,
                count           INTEGER NOT NULL,
                PRIMARY KEY (channel_id, sender_slot)
            )
            """
        )
        await database.conn.execute(
            """
            INSERT INTO sessions (
                channel_id, guild_id, host, port, slot_name, message_style, password_enc, created_at
            )
            VALUES (100, 10, 'localhost', 38281, 'Meow', 'embed', NULL, 'now')
            """
        )
        await database.conn.execute(
            """
            INSERT INTO raspberry_counts (channel_id, sender_slot, count)
            VALUES (100, 'Meow', 2)
            """
        )
        await database.conn.commit()

        await database.migrate()
        rows = await database.fetchall(
            "SELECT room_key, sender_slot, count FROM raspberry_counts"
        )
        assert [(row["room_key"], row["sender_slot"], row["count"]) for row in rows] == [
            ("ap://localhost:38281", "Meow", 2)
        ]
    finally:
        await database.close()
