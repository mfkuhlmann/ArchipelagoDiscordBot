async def test_migrate_creates_all_tables(db):
    tables = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    names = {row["name"] for row in tables}
    assert {"slot_links", "sessions", "muted_slots", "schema_version"}.issubset(names)


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
        "password_enc",
        "created_at",
    }


async def test_muted_slots_columns(db):
    info = await db.fetchall("PRAGMA table_info(muted_slots)")
    cols = {row["name"] for row in info}
    assert cols == {"channel_id", "slot_name"}
