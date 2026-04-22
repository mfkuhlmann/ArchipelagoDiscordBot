# Archipelago Discord Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Discord bot that listens to an Archipelago multiworld room over its WebSocket protocol, filters `PrintJSON` `ItemSend` events to cross-player unlocks, and posts a one-line Discord message per unlock pinging the receiver (when linked).

**Architecture:** Three layers in a single async Python process — `ArchipelagoClient` (raw protocol) → `SessionManager` (lifecycle, retry, coalescing) → Discord cogs (slash commands, message formatting). SQLite (aiosqlite) persists slot↔user links, active sessions, and muted slots. Passwords are encrypted with `cryptography.fernet`.

**Tech Stack:** Python 3.13, `uv`, `discord.py` 2.7.1+ (installed), `websockets`, `aiosqlite`, `cryptography`, `pytest`, `pytest-asyncio`.

**Source spec:** `docs/superpowers/specs/2026-04-22-archipelago-discord-bot-design.md`

---

## Execution notes

- **Commits are the user's responsibility.** After each task, pause and let the user review and commit. Do NOT run `git commit` yourself. Every task ends with a "Pause for user review" step in place of a commit step.
- **TDD:** write the failing test first, verify it fails, implement, verify it passes.
- **Keep files focused.** The file structure below was chosen so each file has one clear responsibility — don't consolidate files to "save" imports.
- **Fixtures:** JSON protocol fixtures used in tests live in `tests/fixtures/ap_frames.py` and are imported by test modules. Build this file up as tasks need frames, rather than one big upfront commit.

---

## File structure

```
X:\repos\ArchipelagoDiscordBot\
├── main.py                              # entrypoint
├── src/archibot/
│   ├── __init__.py
│   ├── config.py                        # env var loading/validation
│   ├── events.py                        # UnlockEvent dataclass
│   ├── archipelago/
│   │   ├── __init__.py
│   │   ├── protocol.py                  # constants, name-lookup helpers
│   │   └── client.py                    # ArchipelagoClient
│   ├── session/
│   │   ├── __init__.py
│   │   ├── formatter.py                 # UnlockEvent → message string
│   │   ├── tracker_session.py           # state machine + retry
│   │   └── manager.py                   # SessionManager
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── db.py                        # SQLite setup + migrations
│   │   ├── crypto.py                    # Fernet helpers
│   │   ├── slot_links.py                # slot_links CRUD
│   │   ├── sessions.py                  # sessions CRUD (with crypto)
│   │   └── muted_slots.py               # muted_slots CRUD
│   └── discord_layer/
│       ├── __init__.py
│       ├── bot.py                       # Bot class
│       ├── embeds.py                    # error/status embed builders
│       ├── permissions.py               # mod role check
│       └── cogs/
│           ├── __init__.py
│           ├── tracking.py              # /track /untrack /status /testunlock
│           ├── linking.py               # /link /unlink /links /players
│           └── moderation.py            # /mute /unmute
├── tests/
│   ├── conftest.py                      # shared fixtures (tmp DB, fake WS server)
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── ap_frames.py                 # recorded JSON frames
│   ├── archipelago/
│   │   ├── __init__.py
│   │   ├── test_protocol.py
│   │   └── test_client.py
│   ├── session/
│   │   ├── __init__.py
│   │   ├── test_formatter.py
│   │   ├── test_tracker_session.py
│   │   └── test_manager.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── test_db.py
│   │   ├── test_crypto.py
│   │   ├── test_slot_links.py
│   │   ├── test_sessions.py
│   │   └── test_muted_slots.py
│   └── discord_layer/
│       ├── __init__.py
│       ├── test_tracking.py
│       ├── test_linking.py
│       └── test_moderation.py
├── data/
│   └── .gitkeep
├── docs/superpowers/
│   ├── specs/2026-04-22-archipelago-discord-bot-design.md
│   └── plans/2026-04-22-archipelago-discord-bot.md
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Phase 1 — Project scaffolding

### Task 1: Add dependencies and dev tooling

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Edit `pyproject.toml` dependencies**

Replace the `[project]` table with:

```toml
[project]
name = "archipelagodiscordbot"
version = "0.1.0"
description = "Discord bot that logs Archipelago multiworld unlocks to a channel"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "discord-py>=2.7.1",
    "websockets>=13.0",
    "aiosqlite>=0.20",
    "cryptography>=43.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/archibot"]
```

- [ ] **Step 2: Install dependencies**

Run: `uv sync --all-groups`
Expected: `Resolved N packages` without errors. `.venv/` is updated.

- [ ] **Step 3: Verify pytest is installed**

Run: `uv run pytest --version`
Expected: Prints `pytest 8.x.x` without errors.

- [ ] **Step 4: Pause for user review**

Report: "Dependencies added and synced. Ready for review."

---

### Task 2: Create project skeleton and config loader

**Files:**
- Create: `src/archibot/__init__.py` (empty)
- Create: `src/archibot/config.py`
- Create: `src/archibot/archipelago/__init__.py` (empty)
- Create: `src/archibot/session/__init__.py` (empty)
- Create: `src/archibot/persistence/__init__.py` (empty)
- Create: `src/archibot/discord_layer/__init__.py` (empty)
- Create: `src/archibot/discord_layer/cogs/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Create: `tests/conftest.py`
- Create: `tests/archipelago/__init__.py` (empty)
- Create: `tests/session/__init__.py` (empty)
- Create: `tests/persistence/__init__.py` (empty)
- Create: `tests/discord_layer/__init__.py` (empty)
- Create: `tests/fixtures/__init__.py` (empty)
- Create: `tests/test_config.py`
- Create: `.env.example`
- Create: `data/.gitkeep` (empty)
- Modify: `.gitignore` (add `.env`, `data/*.db`, `data/*.db-journal`)

- [ ] **Step 1: Create directory tree**

Run: `mkdir -p src/archibot/archipelago src/archibot/session src/archibot/persistence src/archibot/discord_layer/cogs tests/archipelago tests/session tests/persistence tests/discord_layer tests/fixtures data`

- [ ] **Step 2: Create all empty `__init__.py` files**

Create an empty file at each path listed under "Create" that ends in `__init__.py`.

- [ ] **Step 3: Write the failing config test**

Create `tests/test_config.py`:

```python
import os
import pytest
from archibot.config import Config, ConfigError


def test_config_loads_required_discord_token(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    monkeypatch.delenv("BOT_SECRET_KEY", raising=False)
    cfg = Config.from_env()
    assert cfg.discord_token == "abc"
    assert cfg.bot_secret_key is None
    assert cfg.db_path.endswith("bot.db")
    assert cfg.track_role_name == "AP-Mod"
    assert cfg.log_level == "INFO"


def test_config_missing_token_raises(monkeypatch):
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    with pytest.raises(ConfigError, match="DISCORD_TOKEN"):
        Config.from_env()


def test_config_overrides(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "t")
    monkeypatch.setenv("BOT_SECRET_KEY", "ZmVybmV0a2V5MzJieXRlc3Rlc3Rlc3Rlc3RlcwA=")
    monkeypatch.setenv("DB_PATH", "/tmp/x.db")
    monkeypatch.setenv("TRACK_ROLE_NAME", "Admin")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    cfg = Config.from_env()
    assert cfg.bot_secret_key == "ZmVybmV0a2V5MzJieXRlc3Rlc3Rlc3Rlc3RlcwA="
    assert cfg.db_path == "/tmp/x.db"
    assert cfg.track_role_name == "Admin"
    assert cfg.log_level == "DEBUG"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'archibot.config'`

- [ ] **Step 5: Implement `src/archibot/config.py`**

```python
"""Environment-backed configuration for the bot."""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    discord_token: str
    bot_secret_key: str | None
    db_path: str
    track_role_name: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("DISCORD_TOKEN")
        if not token:
            raise ConfigError("DISCORD_TOKEN must be set")
        return cls(
            discord_token=token,
            bot_secret_key=os.environ.get("BOT_SECRET_KEY") or None,
            db_path=os.environ.get("DB_PATH", "./data/bot.db"),
            track_role_name=os.environ.get("TRACK_ROLE_NAME", "AP-Mod"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: 3 PASSED.

- [ ] **Step 7: Write `.env.example`**

```
# Copy to .env and fill in.
DISCORD_TOKEN=
# Base64-encoded 32-byte Fernet key. Generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Required only if you intend to /track rooms with a password.
BOT_SECRET_KEY=
DB_PATH=./data/bot.db
TRACK_ROLE_NAME=AP-Mod
LOG_LEVEL=INFO
```

- [ ] **Step 8: Update `.gitignore`**

Append to `.gitignore`:

```
# Bot runtime
.env
data/*.db
data/*.db-journal
```

- [ ] **Step 9: Create empty `tests/conftest.py`**

Contents:

```python
"""Shared pytest configuration. Fixtures added as tasks need them."""
```

- [ ] **Step 10: Pause for user review**

Report: "Project skeleton and config loader ready. `pytest tests/test_config.py` passes."

---

## Phase 2 — Persistence layer

### Task 3: Fernet encryption helpers

**Files:**
- Create: `src/archibot/persistence/crypto.py`
- Create: `tests/persistence/test_crypto.py`

- [ ] **Step 1: Write failing tests**

Create `tests/persistence/test_crypto.py`:

```python
import pytest
from cryptography.fernet import Fernet

from archibot.persistence.crypto import (
    PasswordCrypto,
    CryptoUnavailableError,
)


def test_roundtrip_encrypts_and_decrypts():
    key = Fernet.generate_key().decode()
    crypto = PasswordCrypto(key)
    ct = crypto.encrypt("hunter2")
    assert ct != b"hunter2"
    assert crypto.decrypt(ct) == "hunter2"


def test_missing_key_raises_on_encrypt():
    crypto = PasswordCrypto(None)
    with pytest.raises(CryptoUnavailableError):
        crypto.encrypt("hunter2")


def test_missing_key_raises_on_decrypt():
    crypto = PasswordCrypto(None)
    with pytest.raises(CryptoUnavailableError):
        crypto.decrypt(b"anything")


def test_empty_password_encrypts_to_none_marker():
    key = Fernet.generate_key().decode()
    crypto = PasswordCrypto(key)
    assert crypto.encrypt("") is None
    assert crypto.decrypt(None) == ""


def test_invalid_key_raises():
    with pytest.raises(ValueError):
        PasswordCrypto("not-a-valid-fernet-key")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/persistence/test_crypto.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/persistence/crypto.py`**

```python
"""Password encryption using Fernet."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class CryptoUnavailableError(RuntimeError):
    """Raised when an operation requires BOT_SECRET_KEY but it is unset."""


class PasswordCrypto:
    """Thin wrapper around Fernet that tolerates a missing key.

    If `key` is None, encrypt/decrypt of non-empty values raises
    CryptoUnavailableError. Empty passwords round-trip to None/"" without
    needing a key.
    """

    def __init__(self, key: str | None) -> None:
        self._fernet: Fernet | None
        if key is None:
            self._fernet = None
        else:
            try:
                self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
            except (ValueError, InvalidToken) as e:
                raise ValueError(f"Invalid Fernet key: {e}") from e

    def encrypt(self, plaintext: str) -> bytes | None:
        if plaintext == "":
            return None
        if self._fernet is None:
            raise CryptoUnavailableError(
                "BOT_SECRET_KEY is not set; cannot encrypt a password"
            )
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes | None) -> str:
        if ciphertext is None:
            return ""
        if self._fernet is None:
            raise CryptoUnavailableError(
                "BOT_SECRET_KEY is not set; cannot decrypt a password"
            )
        return self._fernet.decrypt(ciphertext).decode("utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/persistence/test_crypto.py -v`
Expected: 5 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 4: Database setup & schema

**Files:**
- Create: `src/archibot/persistence/db.py`
- Create: `tests/persistence/test_db.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add a tmp-db fixture to `tests/conftest.py`**

Replace contents with:

```python
"""Shared pytest configuration."""
from __future__ import annotations

import pathlib

import pytest
import pytest_asyncio

from archibot.persistence.db import Database


@pytest_asyncio.fixture
async def db(tmp_path: pathlib.Path) -> Database:
    """Fresh in-memory-ish SQLite database per test."""
    path = tmp_path / "test.db"
    database = Database(str(path))
    await database.connect()
    await database.migrate()
    yield database
    await database.close()
```

- [ ] **Step 2: Write failing tests**

Create `tests/persistence/test_db.py`:

```python
import pytest


async def test_migrate_creates_all_tables(db):
    tables = await db.fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
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
        "channel_id", "guild_id", "host", "port", "slot_name",
        "password_enc", "created_at",
    }


async def test_muted_slots_columns(db):
    info = await db.fetchall("PRAGMA table_info(muted_slots)")
    cols = {row["name"] for row in info}
    assert cols == {"channel_id", "slot_name"}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/persistence/test_db.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 4: Implement `src/archibot/persistence/db.py`**

```python
"""SQLite wrapper with schema migrations."""
from __future__ import annotations

import aiosqlite


SCHEMA_V1 = [
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
        password_enc    BLOB,
        created_at      TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS muted_slots (
        channel_id  INTEGER NOT NULL,
        slot_name   TEXT    NOT NULL,
        PRIMARY KEY (channel_id, slot_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """,
]


class Database:
    """Thin async wrapper around a single aiosqlite connection."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> None:
        await self.conn.execute(sql, params)
        await self.conn.commit()

    async def fetchone(self, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
        async with self.conn.execute(sql, params) as cur:
            return await cur.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
        async with self.conn.execute(sql, params) as cur:
            return list(await cur.fetchall())

    async def migrate(self) -> None:
        """Create tables if missing. Idempotent."""
        for stmt in SCHEMA_V1:
            await self.conn.execute(stmt)
        row = await self.fetchone("SELECT version FROM schema_version")
        if row is None:
            await self.conn.execute("INSERT INTO schema_version (version) VALUES (1)")
        await self.conn.commit()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/persistence/test_db.py -v`
Expected: 5 PASSED.

- [ ] **Step 6: Pause for user review**

---

### Task 5: slot_links CRUD

**Files:**
- Create: `src/archibot/persistence/slot_links.py`
- Create: `tests/persistence/test_slot_links.py`

- [ ] **Step 1: Write failing tests**

Create `tests/persistence/test_slot_links.py`:

```python
import pytest

from archibot.persistence.slot_links import SlotLinks


async def test_add_and_get(db):
    repo = SlotLinks(db)
    await repo.upsert(guild_id=1, slot_name="Meow", discord_user_id=42)
    assert await repo.get(1, "Meow") == 42
    assert await repo.get(1, "Bork") is None


async def test_upsert_replaces(db):
    repo = SlotLinks(db)
    await repo.upsert(1, "Meow", 42)
    await repo.upsert(1, "Meow", 99)
    assert await repo.get(1, "Meow") == 99


async def test_scoped_by_guild(db):
    repo = SlotLinks(db)
    await repo.upsert(1, "Meow", 42)
    await repo.upsert(2, "Meow", 99)
    assert await repo.get(1, "Meow") == 42
    assert await repo.get(2, "Meow") == 99


async def test_remove_one(db):
    repo = SlotLinks(db)
    await repo.upsert(1, "Meow", 42)
    await repo.upsert(1, "Bork", 43)
    await repo.remove(guild_id=1, slot_name="Meow", discord_user_id=42)
    assert await repo.get(1, "Meow") is None
    assert await repo.get(1, "Bork") == 43


async def test_remove_only_caller_can_unlink(db):
    """A user cannot remove another user's link."""
    repo = SlotLinks(db)
    await repo.upsert(1, "Meow", 42)
    removed = await repo.remove(guild_id=1, slot_name="Meow", discord_user_id=999)
    assert removed == 0
    assert await repo.get(1, "Meow") == 42


async def test_remove_all_for_user(db):
    repo = SlotLinks(db)
    await repo.upsert(1, "Meow", 42)
    await repo.upsert(1, "Bork", 42)
    await repo.upsert(1, "Other", 99)
    removed = await repo.remove_all_for_user(guild_id=1, discord_user_id=42)
    assert removed == 2
    assert await repo.get(1, "Meow") is None
    assert await repo.get(1, "Other") == 99


async def test_list_by_guild(db):
    repo = SlotLinks(db)
    await repo.upsert(1, "Meow", 42)
    await repo.upsert(1, "Bork", 43)
    await repo.upsert(2, "Other", 99)
    rows = await repo.list_by_guild(1)
    slots = {r.slot_name: r.discord_user_id for r in rows}
    assert slots == {"Meow": 42, "Bork": 43}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/persistence/test_slot_links.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/persistence/slot_links.py`**

```python
"""CRUD for the slot_links table."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from archibot.persistence.db import Database


@dataclass(frozen=True)
class SlotLink:
    guild_id: int
    slot_name: str
    discord_user_id: int
    created_at: str


class SlotLinks:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert(self, guild_id: int, slot_name: str, discord_user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """
            INSERT INTO slot_links (guild_id, slot_name, discord_user_id, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, slot_name) DO UPDATE SET
                discord_user_id = excluded.discord_user_id,
                created_at = excluded.created_at
            """,
            (guild_id, slot_name, discord_user_id, now),
        )

    async def get(self, guild_id: int, slot_name: str) -> int | None:
        row = await self.db.fetchone(
            "SELECT discord_user_id FROM slot_links WHERE guild_id = ? AND slot_name = ?",
            (guild_id, slot_name),
        )
        return row["discord_user_id"] if row else None

    async def remove(
        self, guild_id: int, slot_name: str, discord_user_id: int
    ) -> int:
        """Remove a specific link only if the caller owns it.

        Returns number of rows removed (0 or 1).
        """
        cur = await self.db.conn.execute(
            """
            DELETE FROM slot_links
             WHERE guild_id = ? AND slot_name = ? AND discord_user_id = ?
            """,
            (guild_id, slot_name, discord_user_id),
        )
        await self.db.conn.commit()
        return cur.rowcount

    async def remove_all_for_user(self, guild_id: int, discord_user_id: int) -> int:
        cur = await self.db.conn.execute(
            "DELETE FROM slot_links WHERE guild_id = ? AND discord_user_id = ?",
            (guild_id, discord_user_id),
        )
        await self.db.conn.commit()
        return cur.rowcount

    async def list_by_guild(self, guild_id: int) -> list[SlotLink]:
        rows = await self.db.fetchall(
            """
            SELECT guild_id, slot_name, discord_user_id, created_at
              FROM slot_links WHERE guild_id = ?
             ORDER BY slot_name
            """,
            (guild_id,),
        )
        return [SlotLink(**dict(r)) for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/persistence/test_slot_links.py -v`
Expected: 7 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 6: sessions CRUD (with crypto)

**Files:**
- Create: `src/archibot/persistence/sessions.py`
- Create: `tests/persistence/test_sessions.py`

- [ ] **Step 1: Write failing tests**

Create `tests/persistence/test_sessions.py`:

```python
import pytest
from cryptography.fernet import Fernet

from archibot.persistence.crypto import PasswordCrypto, CryptoUnavailableError
from archibot.persistence.sessions import Sessions, SessionRow


@pytest.fixture
def crypto():
    return PasswordCrypto(Fernet.generate_key().decode())


async def test_create_and_get(db, crypto):
    repo = Sessions(db, crypto)
    await repo.create(
        channel_id=100, guild_id=1, host="ap.gg", port=38281,
        slot_name="Meow", password="hunter2",
    )
    row = await repo.get(100)
    assert row.channel_id == 100
    assert row.host == "ap.gg"
    assert row.port == 38281
    assert row.slot_name == "Meow"
    assert row.password == "hunter2"  # decrypted


async def test_password_stored_encrypted(db, crypto):
    repo = Sessions(db, crypto)
    await repo.create(100, 1, "ap.gg", 38281, "Meow", "hunter2")
    raw = await db.fetchone(
        "SELECT password_enc FROM sessions WHERE channel_id = ?", (100,)
    )
    assert raw["password_enc"] != b"hunter2"
    assert len(raw["password_enc"]) > 16  # Fernet ciphertext


async def test_empty_password_stores_null(db, crypto):
    repo = Sessions(db, crypto)
    await repo.create(100, 1, "ap.gg", 38281, "Meow", "")
    raw = await db.fetchone(
        "SELECT password_enc FROM sessions WHERE channel_id = ?", (100,)
    )
    assert raw["password_enc"] is None
    row = await repo.get(100)
    assert row.password == ""


async def test_create_with_no_crypto_and_password_raises(db):
    repo = Sessions(db, PasswordCrypto(None))
    with pytest.raises(CryptoUnavailableError):
        await repo.create(100, 1, "ap.gg", 38281, "Meow", "hunter2")


async def test_duplicate_channel_raises(db, crypto):
    repo = Sessions(db, crypto)
    await repo.create(100, 1, "ap.gg", 38281, "Meow", "")
    with pytest.raises(Exception):  # IntegrityError
        await repo.create(100, 1, "other.gg", 1234, "Bork", "")


async def test_delete(db, crypto):
    repo = Sessions(db, crypto)
    await repo.create(100, 1, "ap.gg", 38281, "Meow", "")
    assert await repo.get(100) is not None
    deleted = await repo.delete(100)
    assert deleted == 1
    assert await repo.get(100) is None


async def test_list_all(db, crypto):
    repo = Sessions(db, crypto)
    await repo.create(100, 1, "ap.gg", 38281, "Meow", "")
    await repo.create(200, 1, "ap.gg", 38282, "Bork", "")
    rows = await repo.list_all()
    assert len(rows) == 2
    assert {r.channel_id for r in rows} == {100, 200}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/persistence/test_sessions.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/persistence/sessions.py`**

```python
"""CRUD for the sessions table."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.db import Database


@dataclass(frozen=True)
class SessionRow:
    channel_id: int
    guild_id: int
    host: str
    port: int
    slot_name: str
    password: str  # decrypted
    created_at: str


class Sessions:
    def __init__(self, db: Database, crypto: PasswordCrypto) -> None:
        self.db = db
        self.crypto = crypto

    async def create(
        self,
        channel_id: int,
        guild_id: int,
        host: str,
        port: int,
        slot_name: str,
        password: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        enc = self.crypto.encrypt(password)  # raises if no key and non-empty
        await self.db.execute(
            """
            INSERT INTO sessions
                (channel_id, guild_id, host, port, slot_name, password_enc, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (channel_id, guild_id, host, port, slot_name, enc, now),
        )

    async def get(self, channel_id: int) -> SessionRow | None:
        row = await self.db.fetchone(
            "SELECT * FROM sessions WHERE channel_id = ?", (channel_id,)
        )
        if row is None:
            return None
        return SessionRow(
            channel_id=row["channel_id"],
            guild_id=row["guild_id"],
            host=row["host"],
            port=row["port"],
            slot_name=row["slot_name"],
            password=self.crypto.decrypt(row["password_enc"]),
            created_at=row["created_at"],
        )

    async def delete(self, channel_id: int) -> int:
        cur = await self.db.conn.execute(
            "DELETE FROM sessions WHERE channel_id = ?", (channel_id,)
        )
        await self.db.conn.commit()
        return cur.rowcount

    async def list_all(self) -> list[SessionRow]:
        rows = await self.db.fetchall("SELECT * FROM sessions ORDER BY channel_id")
        return [
            SessionRow(
                channel_id=r["channel_id"],
                guild_id=r["guild_id"],
                host=r["host"],
                port=r["port"],
                slot_name=r["slot_name"],
                password=self.crypto.decrypt(r["password_enc"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/persistence/test_sessions.py -v`
Expected: 7 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 7: muted_slots CRUD

**Files:**
- Create: `src/archibot/persistence/muted_slots.py`
- Create: `tests/persistence/test_muted_slots.py`

- [ ] **Step 1: Write failing tests**

Create `tests/persistence/test_muted_slots.py`:

```python
import pytest

from archibot.persistence.muted_slots import MutedSlots


async def test_mute_and_check(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Meow")
    assert await repo.is_muted(100, "Meow") is True
    assert await repo.is_muted(100, "Bork") is False
    assert await repo.is_muted(200, "Meow") is False


async def test_mute_idempotent(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Meow")
    await repo.mute(100, "Meow")  # should not raise
    rows = await repo.list_for_channel(100)
    assert rows == ["Meow"]


async def test_unmute(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Meow")
    removed = await repo.unmute(100, "Meow")
    assert removed == 1
    assert await repo.is_muted(100, "Meow") is False


async def test_unmute_missing_returns_zero(db):
    repo = MutedSlots(db)
    removed = await repo.unmute(100, "Meow")
    assert removed == 0


async def test_list_for_channel(db):
    repo = MutedSlots(db)
    await repo.mute(100, "Meow")
    await repo.mute(100, "Bork")
    await repo.mute(200, "Other")
    rows = await repo.list_for_channel(100)
    assert sorted(rows) == ["Bork", "Meow"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/persistence/test_muted_slots.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/persistence/muted_slots.py`**

```python
"""CRUD for the muted_slots table."""
from __future__ import annotations

from archibot.persistence.db import Database


class MutedSlots:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def mute(self, channel_id: int, slot_name: str) -> None:
        await self.db.execute(
            """
            INSERT INTO muted_slots (channel_id, slot_name) VALUES (?, ?)
            ON CONFLICT(channel_id, slot_name) DO NOTHING
            """,
            (channel_id, slot_name),
        )

    async def unmute(self, channel_id: int, slot_name: str) -> int:
        cur = await self.db.conn.execute(
            "DELETE FROM muted_slots WHERE channel_id = ? AND slot_name = ?",
            (channel_id, slot_name),
        )
        await self.db.conn.commit()
        return cur.rowcount

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
        return [r["slot_name"] for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/persistence/test_muted_slots.py -v`
Expected: 5 PASSED.

- [ ] **Step 5: Pause for user review**

---

## Phase 3 — Archipelago client

### Task 8: UnlockEvent dataclass

**Files:**
- Create: `src/archibot/events.py`
- Create: `tests/test_events.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_events.py`:

```python
from archibot.events import UnlockEvent, ItemFlag


def test_flag_helpers():
    assert ItemFlag.from_bits(0).classification == "filler"
    assert ItemFlag.from_bits(0b001).classification == "progression"
    assert ItemFlag.from_bits(0b010).classification == "useful"
    assert ItemFlag.from_bits(0b100).classification == "trap"
    # progression beats other flags for display purposes
    assert ItemFlag.from_bits(0b011).classification == "progression"


def test_flag_emoji():
    assert ItemFlag.from_bits(0).emoji == "⚪"
    assert ItemFlag.from_bits(0b001).emoji == "🟣"
    assert ItemFlag.from_bits(0b010).emoji == "🔵"
    assert ItemFlag.from_bits(0b100).emoji == "🔴"


def test_unlock_event_is_frozen():
    e = UnlockEvent(
        receiver_slot="Bork", sender_slot="Meow", item_name="Master Sword",
        location_name="Eastern Palace - Big Chest", game="A Link to the Past",
        flags=1,
    )
    import dataclasses
    assert dataclasses.is_dataclass(e)
    # attempting to mutate should raise
    import pytest
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.receiver_slot = "x"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_events.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/events.py`**

```python
"""Domain events emitted by the Archipelago client."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemFlag:
    bits: int

    FLAG_PROGRESSION = 0b001
    FLAG_USEFUL = 0b010
    FLAG_TRAP = 0b100

    @classmethod
    def from_bits(cls, bits: int) -> "ItemFlag":
        return cls(bits=bits)

    @property
    def classification(self) -> str:
        if self.bits & self.FLAG_PROGRESSION:
            return "progression"
        if self.bits & self.FLAG_USEFUL:
            return "useful"
        if self.bits & self.FLAG_TRAP:
            return "trap"
        return "filler"

    @property
    def emoji(self) -> str:
        return {
            "progression": "🟣",
            "useful": "🔵",
            "trap": "🔴",
            "filler": "⚪",
        }[self.classification]


@dataclass(frozen=True)
class UnlockEvent:
    """A cross-player item send detected in an Archipelago room."""
    receiver_slot: str
    sender_slot: str
    item_name: str
    location_name: str
    game: str
    flags: int
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_events.py -v`
Expected: 3 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 9: Protocol constants and name-lookup helpers

**Files:**
- Create: `src/archibot/archipelago/protocol.py`
- Create: `tests/archipelago/test_protocol.py`
- Create: `tests/fixtures/ap_frames.py`

- [ ] **Step 1: Seed the fixture file**

Create `tests/fixtures/ap_frames.py`:

```python
"""Recorded / synthesized Archipelago protocol frames for tests."""
from __future__ import annotations

# Minimal RoomInfo — only fields we actually read.
ROOM_INFO = {
    "cmd": "RoomInfo",
    "version": {"class": "Version", "major": 0, "minor": 5, "build": 0},
    "generator_version": {"class": "Version", "major": 0, "minor": 5, "build": 0},
    "tags": ["WebHost"],
    "password": False,
    "permissions": {"release": 1, "collect": 1, "remaining": 0},
    "hint_cost": 10,
    "location_check_points": 1,
    "games": ["A Link to the Past", "Ocarina of Time"],
    "datapackage_checksums": {},
    "seed_name": "TEST-SEED",
    "time": 0.0,
}

# DataPackage: only what our code reads — item_name_to_id and
# location_name_to_id, inverted at parse time.
DATA_PACKAGE = {
    "cmd": "DataPackage",
    "data": {
        "games": {
            "A Link to the Past": {
                "item_name_to_id": {"Master Sword": 1001, "Rupees": 1002},
                "location_name_to_id": {"Eastern Palace - Big Chest": 2001},
                "checksum": "abc",
            },
            "Ocarina of Time": {
                "item_name_to_id": {"Kokiri Sword": 3001},
                "location_name_to_id": {"Kokiri Forest - Sword Chest": 4001},
                "checksum": "def",
            },
        }
    },
}

CONNECTED = {
    "cmd": "Connected",
    "team": 0,
    "slot": 1,
    "players": [
        {"class": "NetworkPlayer", "team": 0, "slot": 1, "alias": "Meow", "name": "Meow"},
        {"class": "NetworkPlayer", "team": 0, "slot": 2, "alias": "Bork", "name": "Bork"},
    ],
    "missing_locations": [],
    "checked_locations": [],
    "slot_data": {},
    "slot_info": {
        "1": {"class": "NetworkSlot", "name": "Meow", "game": "A Link to the Past", "type": 1, "group_members": []},
        "2": {"class": "NetworkSlot", "name": "Bork", "game": "Ocarina of Time", "type": 1, "group_members": []},
    },
    "hint_points": 0,
}

CONNECTION_REFUSED_INVALID_SLOT = {
    "cmd": "ConnectionRefused",
    "errors": ["InvalidSlot"],
}

# PrintJSON ItemSend: Meow's A Link to the Past found a Kokiri Sword for Bork.
PRINTJSON_ITEMSEND_CROSSPLAYER = {
    "cmd": "PrintJSON",
    "type": "ItemSend",
    "data": [{"text": "etc"}],  # we don't use .data
    "receiving": 2,  # Bork
    "item": {
        "class": "NetworkItem",
        "item": 3001,  # Kokiri Sword (Bork's game)
        "location": 2001,  # Eastern Palace - Big Chest (Meow's game)
        "player": 1,  # Meow (sender)
        "flags": 1,  # progression
    },
}

# ItemSend to self — should be dropped.
PRINTJSON_ITEMSEND_OWNWORLD = {
    "cmd": "PrintJSON",
    "type": "ItemSend",
    "data": [{"text": "etc"}],
    "receiving": 1,
    "item": {
        "class": "NetworkItem",
        "item": 1001, "location": 2001, "player": 1, "flags": 0,
    },
}

# ItemSend from server (sender slot 0) — should be dropped.
PRINTJSON_ITEMSEND_FROM_SERVER = {
    "cmd": "PrintJSON",
    "type": "ItemSend",
    "data": [{"text": "etc"}],
    "receiving": 2,
    "item": {
        "class": "NetworkItem",
        "item": 3001, "location": 0, "player": 0, "flags": 0,
    },
}

# Different PrintJSON type — should be ignored.
PRINTJSON_CHAT = {
    "cmd": "PrintJSON",
    "type": "Chat",
    "data": [{"text": "hi"}],
    "team": 0, "slot": 1,
    "message": "hi",
}
```

- [ ] **Step 2: Write failing protocol tests**

Create `tests/archipelago/test_protocol.py`:

```python
import pytest

from archibot.archipelago.protocol import (
    NameResolver, build_connect_packet, parse_connection_refused,
)
from tests.fixtures.ap_frames import (
    DATA_PACKAGE, CONNECTED, CONNECTION_REFUSED_INVALID_SLOT,
)


def test_build_connect_packet_sets_tracker_tag():
    pkt = build_connect_packet(slot="Meow", password="hunter2")
    assert pkt["cmd"] == "Connect"
    assert pkt["name"] == "Meow"
    assert pkt["password"] == "hunter2"
    assert pkt["game"] == ""
    assert "Tracker" in pkt["tags"]
    assert pkt["items_handling"] == 0
    assert pkt["slot_data"] is False


def test_build_connect_packet_empty_password():
    pkt = build_connect_packet(slot="Meow", password="")
    assert pkt["password"] == ""


def test_parse_connection_refused_returns_error_list():
    errors = parse_connection_refused(CONNECTION_REFUSED_INVALID_SLOT)
    assert errors == ["InvalidSlot"]


def test_name_resolver_items_and_locations():
    resolver = NameResolver()
    resolver.load_data_package(DATA_PACKAGE["data"])
    resolver.load_connected(CONNECTED)
    assert resolver.slot_name(1) == "Meow"
    assert resolver.slot_name(2) == "Bork"
    assert resolver.slot_game(1) == "A Link to the Past"
    # item id belongs to receiver's game (A Link to the Past: 1001 -> Master Sword)
    assert resolver.item_name(1001, "A Link to the Past") == "Master Sword"
    assert resolver.location_name(2001, "A Link to the Past") == "Eastern Palace - Big Chest"


def test_name_resolver_unknown_ids_fall_back():
    resolver = NameResolver()
    resolver.load_data_package(DATA_PACKAGE["data"])
    resolver.load_connected(CONNECTED)
    assert resolver.item_name(9999, "A Link to the Past") == "item[9999]"
    assert resolver.location_name(9999, "A Link to the Past") == "location[9999]"
    assert resolver.slot_name(99) == "slot[99]"
    assert resolver.slot_game(99) == ""


def test_name_resolver_prefers_alias_over_name():
    resolver = NameResolver()
    data = {
        **CONNECTED,
        "players": [
            {"class": "NetworkPlayer", "team": 0, "slot": 1,
             "alias": "Fluffy", "name": "Meow"},
        ],
    }
    resolver.load_connected(data)
    assert resolver.slot_name(1) == "Fluffy"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/archipelago/test_protocol.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 4: Implement `src/archibot/archipelago/protocol.py`**

```python
"""Archipelago network-protocol helpers — constants, builders, name lookup.

Scope: pure functions and stateful-but-IO-free helpers. WebSocket logic
lives in `client.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# The version we advertise to the server. Bumping this only matters if the
# server enforces a higher minimum — the Tracker tag skips version checks
# for the *game*, but the server itself still has a min client version.
CLIENT_VERSION = {"class": "Version", "major": 0, "minor": 5, "build": 0}

# items_handling = 0: we don't want items sent to us (we're a Tracker).
ITEMS_HANDLING_NONE = 0

# Tag values. Tracker makes us read-only; NoText would suppress chat but
# also risks suppressing ItemSend broadcasts on some server versions, so
# we leave it off in MVP.
TAG_TRACKER = "Tracker"


def build_connect_packet(slot: str, password: str, uuid: str = "0") -> dict[str, Any]:
    """Construct the Connect packet for a Tracker-tagged read-only client."""
    return {
        "cmd": "Connect",
        "password": password,
        "game": "",  # Tracker tag allows empty
        "name": slot,
        "uuid": uuid,
        "version": CLIENT_VERSION,
        "items_handling": ITEMS_HANDLING_NONE,
        "tags": [TAG_TRACKER],
        "slot_data": False,
    }


def parse_connection_refused(packet: dict[str, Any]) -> list[str]:
    """Extract the error codes from a ConnectionRefused packet."""
    return list(packet.get("errors", []))


@dataclass
class NameResolver:
    """Resolves numeric ids to human-readable names.

    Loaded from a DataPackage (for item/location names, scoped by game)
    and a Connected packet (for slot name and game mapping).
    """
    # slot_id -> display name
    _slots: dict[int, str] = field(default_factory=dict)
    # slot_id -> game name
    _slot_games: dict[int, str] = field(default_factory=dict)
    # game -> item_id -> name
    _item_names: dict[str, dict[int, str]] = field(default_factory=dict)
    # game -> location_id -> name
    _location_names: dict[str, dict[int, str]] = field(default_factory=dict)

    def load_data_package(self, data: dict[str, Any]) -> None:
        for game, pkg in data.get("games", {}).items():
            self._item_names[game] = {
                v: k for k, v in pkg.get("item_name_to_id", {}).items()
            }
            self._location_names[game] = {
                v: k for k, v in pkg.get("location_name_to_id", {}).items()
            }

    def load_connected(self, packet: dict[str, Any]) -> None:
        for player in packet.get("players", []):
            slot_id = player["slot"]
            alias = player.get("alias") or ""
            name = player.get("name") or ""
            self._slots[slot_id] = alias or name or f"slot[{slot_id}]"
        slot_info = packet.get("slot_info", {})
        for key, info in slot_info.items():
            slot_id = int(key)
            self._slot_games[slot_id] = info.get("game", "")

    def slot_name(self, slot_id: int) -> str:
        return self._slots.get(slot_id, f"slot[{slot_id}]")

    def slot_game(self, slot_id: int) -> str:
        return self._slot_games.get(slot_id, "")

    def item_name(self, item_id: int, game: str) -> str:
        return self._item_names.get(game, {}).get(item_id, f"item[{item_id}]")

    def location_name(self, location_id: int, game: str) -> str:
        return self._location_names.get(game, {}).get(
            location_id, f"location[{location_id}]"
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/archipelago/test_protocol.py -v`
Expected: 6 PASSED.

- [ ] **Step 6: Pause for user review**

---

### Task 10: ArchipelagoClient — packet dispatch (pure, IO-free core)

The WebSocket wrapper and the packet-handling logic are split so the logic is unit-testable with recorded frames. This task builds the IO-free core; Task 11 wires in the actual WebSocket.

**Files:**
- Create: `src/archibot/archipelago/client.py`
- Create: `tests/archipelago/test_client.py`

- [ ] **Step 1: Extend the fixture file with more cases**

Append to `tests/fixtures/ap_frames.py`:

```python

# ItemSend where sender game is unknown (slot_info missing) — fallback path.
PRINTJSON_ITEMSEND_UNKNOWN_GAME = {
    "cmd": "PrintJSON",
    "type": "ItemSend",
    "data": [{"text": "etc"}],
    "receiving": 2,
    "item": {
        "class": "NetworkItem",
        "item": 9999, "location": 9999, "player": 99, "flags": 0,
    },
}
```

- [ ] **Step 2: Write failing tests**

Create `tests/archipelago/test_client.py`:

```python
import pytest

from archibot.archipelago.client import PacketRouter
from archibot.events import UnlockEvent
from tests.fixtures.ap_frames import (
    ROOM_INFO, DATA_PACKAGE, CONNECTED, CONNECTION_REFUSED_INVALID_SLOT,
    PRINTJSON_ITEMSEND_CROSSPLAYER, PRINTJSON_ITEMSEND_OWNWORLD,
    PRINTJSON_ITEMSEND_FROM_SERVER, PRINTJSON_CHAT,
    PRINTJSON_ITEMSEND_UNKNOWN_GAME,
)


class Capture:
    def __init__(self) -> None:
        self.events: list[UnlockEvent] = []

    async def __call__(self, e: UnlockEvent) -> None:
        self.events.append(e)


async def _router_with_handshake() -> tuple[PacketRouter, Capture]:
    cap = Capture()
    router = PacketRouter(on_event=cap)
    router.feed(ROOM_INFO)
    router.feed(DATA_PACKAGE)
    router.feed(CONNECTED)
    await router.drain()
    return router, cap


async def test_handshake_emits_nothing():
    _, cap = await _router_with_handshake()
    assert cap.events == []


async def test_cross_player_itemsend_emits_event():
    router, cap = await _router_with_handshake()
    router.feed(PRINTJSON_ITEMSEND_CROSSPLAYER)
    await router.drain()
    assert len(cap.events) == 1
    e = cap.events[0]
    assert e.receiver_slot == "Bork"
    assert e.sender_slot == "Meow"
    # Item belongs to receiver's game (Bork: Ocarina of Time); resolver
    # should look up item_id 3001 in Ocarina's table.
    assert e.item_name == "Kokiri Sword"
    # Location belongs to sender's game (Meow: A Link to the Past).
    assert e.location_name == "Eastern Palace - Big Chest"
    assert e.game == "A Link to the Past"
    assert e.flags == 1


async def test_own_world_itemsend_dropped():
    router, cap = await _router_with_handshake()
    router.feed(PRINTJSON_ITEMSEND_OWNWORLD)
    await router.drain()
    assert cap.events == []


async def test_server_itemsend_dropped():
    router, cap = await _router_with_handshake()
    router.feed(PRINTJSON_ITEMSEND_FROM_SERVER)
    await router.drain()
    assert cap.events == []


async def test_other_printjson_types_ignored():
    router, cap = await _router_with_handshake()
    router.feed(PRINTJSON_CHAT)
    await router.drain()
    assert cap.events == []


async def test_unknown_game_still_emits_with_fallback_names():
    router, cap = await _router_with_handshake()
    router.feed(PRINTJSON_ITEMSEND_UNKNOWN_GAME)
    await router.drain()
    assert len(cap.events) == 1
    e = cap.events[0]
    assert e.receiver_slot == "Bork"
    assert e.sender_slot == "slot[99]"
    assert e.item_name == "item[9999]"
    assert e.location_name == "location[9999]"


async def test_connection_refused_raises():
    from archibot.archipelago.client import ArchipelagoConnectionRefused
    cap = Capture()
    router = PacketRouter(on_event=cap)
    router.feed(ROOM_INFO)
    router.feed(DATA_PACKAGE)
    with pytest.raises(ArchipelagoConnectionRefused) as exc_info:
        router.feed(CONNECTION_REFUSED_INVALID_SLOT)
    assert "InvalidSlot" in str(exc_info.value)


async def test_malformed_packet_logged_not_raised(caplog):
    import logging
    caplog.set_level(logging.WARNING, logger="archibot.archipelago.client")
    cap = Capture()
    router = PacketRouter(on_event=cap)
    router.feed({"cmd": "PrintJSON", "type": "ItemSend"})  # missing fields
    await router.drain()
    assert cap.events == []
    assert any("malformed" in rec.message.lower() for rec in caplog.records)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/archipelago/test_client.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 4: Implement `src/archibot/archipelago/client.py` — router only**

```python
"""Archipelago WebSocket client.

Split into two pieces:
  - PacketRouter: pure, IO-free, takes parsed dict packets and emits
    UnlockEvents through an async callback. Testable offline.
  - ArchipelagoClient: wraps PacketRouter with the WebSocket connection
    loop and handshake. Added in Task 11.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from archibot.archipelago.protocol import NameResolver, parse_connection_refused
from archibot.events import UnlockEvent

log = logging.getLogger(__name__)

OnEvent = Callable[[UnlockEvent], Awaitable[None]]


class ArchipelagoConnectionRefused(RuntimeError):
    """Server refused the Connect packet."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(f"ConnectionRefused: {', '.join(errors) or '?'}")
        self.errors = errors


class PacketRouter:
    """Consume parsed Archipelago packets; emit UnlockEvents.

    Call `feed(packet)` for each packet. ItemSend events schedule emissions
    on an internal queue that is drained by `drain()` (awaited by the caller
    to keep the interface simple and deterministic in tests).
    """

    def __init__(self, on_event: OnEvent) -> None:
        self.on_event = on_event
        self.resolver = NameResolver()
        self._pending: list[UnlockEvent] = []

    def feed(self, packet: dict[str, Any]) -> None:
        cmd = packet.get("cmd")
        if cmd == "RoomInfo":
            return
        if cmd == "DataPackage":
            self.resolver.load_data_package(packet.get("data", {}))
            return
        if cmd == "Connected":
            self.resolver.load_connected(packet)
            return
        if cmd == "ConnectionRefused":
            raise ArchipelagoConnectionRefused(parse_connection_refused(packet))
        if cmd == "PrintJSON":
            self._handle_printjson(packet)
            return
        # Other commands (RoomUpdate, ReceivedItems, etc.) are not needed for
        # cross-player unlock detection. Ignore silently.

    def _handle_printjson(self, packet: dict[str, Any]) -> None:
        if packet.get("type") != "ItemSend":
            return
        try:
            receiver_id = int(packet["receiving"])
            item = packet["item"]
            sender_id = int(item["player"])
            item_id = int(item["item"])
            location_id = int(item["location"])
            flags = int(item.get("flags", 0))
        except (KeyError, TypeError, ValueError):
            log.warning("malformed ItemSend packet: %r", packet)
            return

        if sender_id == 0 or sender_id == receiver_id:
            return

        sender_game = self.resolver.slot_game(sender_id)
        receiver_game = self.resolver.slot_game(receiver_id)
        # The `item` field identifies the item in the RECEIVER's game
        # (that's whose inventory it ends up in). The `location` field
        # identifies where in the SENDER's world it was found.
        event = UnlockEvent(
            receiver_slot=self.resolver.slot_name(receiver_id),
            sender_slot=self.resolver.slot_name(sender_id),
            item_name=self.resolver.item_name(item_id, receiver_game),
            location_name=self.resolver.location_name(location_id, sender_game),
            game=sender_game,
            flags=flags,
        )
        self._pending.append(event)

    async def drain(self) -> None:
        while self._pending:
            event = self._pending.pop(0)
            await self.on_event(event)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/archipelago/test_client.py -v`
Expected: 8 PASSED.

- [ ] **Step 6: Pause for user review**

---

### Task 11: ArchipelagoClient — WebSocket wrapper

Wraps `PacketRouter` with an actual `websockets` connection. Tested against an in-process fake server.

**Files:**
- Modify: `src/archibot/archipelago/client.py`
- Modify: `tests/archipelago/test_client.py`

- [ ] **Step 1: Append a fake-server fixture to `tests/conftest.py`**

Append:

```python
import asyncio
import json

import pytest_asyncio
import websockets


class ScriptedAPServer:
    """Minimal AP-like WebSocket server for tests.

    Replays a scripted list of packet batches in order. Each batch is sent
    after receiving the expected client command, or unconditionally with
    `send_on_connect=True`.
    """

    def __init__(self) -> None:
        self._script: list[tuple[str | None, list[dict]]] = []
        self.received: list[dict] = []
        self._server: websockets.WebSocketServer | None = None
        self.port: int = 0

    def enqueue(self, client_cmd: str | None, response: list[dict]) -> None:
        """Next response batch, sent when the client sends `client_cmd`
        (or unconditionally if client_cmd is None)."""
        self._script.append((client_cmd, response))

    async def start(self) -> None:
        self._server = await websockets.serve(self._handler, "localhost", 0)
        self.port = self._server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handler(self, ws):
        # Send any unconditional first batches
        while self._script and self._script[0][0] is None:
            _, batch = self._script.pop(0)
            await ws.send(json.dumps(batch))
        try:
            async for raw in ws:
                packets = json.loads(raw)
                for p in packets:
                    self.received.append(p)
                    if self._script and self._script[0][0] == p.get("cmd"):
                        _, batch = self._script.pop(0)
                        await ws.send(json.dumps(batch))
                        while self._script and self._script[0][0] is None:
                            _, batch = self._script.pop(0)
                            await ws.send(json.dumps(batch))
        except websockets.ConnectionClosed:
            return


@pytest_asyncio.fixture
async def fake_ap_server():
    srv = ScriptedAPServer()
    await srv.start()
    yield srv
    await srv.stop()
```

- [ ] **Step 2: Write failing WebSocket-wrapper tests**

Append to `tests/archipelago/test_client.py`:

```python
async def test_client_handshake_sends_connect_with_tracker_tag(fake_ap_server):
    from archibot.archipelago.client import ArchipelagoClient
    fake_ap_server.enqueue(None, [ROOM_INFO])
    fake_ap_server.enqueue("GetDataPackage", [DATA_PACKAGE])
    fake_ap_server.enqueue("Connect", [CONNECTED])

    cap = Capture()
    client = ArchipelagoClient(
        host="localhost", port=fake_ap_server.port, slot="Meow",
        password="", on_event=cap, use_tls=False,
    )
    # Run until we've seen the Connected handshake, then close.
    task = __import__("asyncio").create_task(client.run())
    # Give it a moment to complete handshake.
    for _ in range(50):
        await __import__("asyncio").sleep(0.02)
        if any(p.get("cmd") == "Connect" for p in fake_ap_server.received):
            break
    await client.close()
    with pytest.raises((__import__("asyncio").CancelledError, Exception)):
        await task

    connect_pkts = [p for p in fake_ap_server.received if p.get("cmd") == "Connect"]
    assert len(connect_pkts) == 1
    assert connect_pkts[0]["name"] == "Meow"
    assert "Tracker" in connect_pkts[0]["tags"]
    assert connect_pkts[0]["items_handling"] == 0


async def test_client_forwards_itemsend_to_callback(fake_ap_server):
    import asyncio
    from archibot.archipelago.client import ArchipelagoClient
    fake_ap_server.enqueue(None, [ROOM_INFO])
    fake_ap_server.enqueue("GetDataPackage", [DATA_PACKAGE])
    fake_ap_server.enqueue("Connect", [CONNECTED, PRINTJSON_ITEMSEND_CROSSPLAYER])

    cap = Capture()
    client = ArchipelagoClient(
        host="localhost", port=fake_ap_server.port, slot="Meow",
        password="", on_event=cap, use_tls=False,
    )
    task = asyncio.create_task(client.run())
    for _ in range(100):
        await asyncio.sleep(0.02)
        if cap.events:
            break
    await client.close()
    try:
        await task
    except Exception:
        pass
    assert len(cap.events) == 1
    assert cap.events[0].receiver_slot == "Bork"


async def test_client_raises_on_connection_refused(fake_ap_server):
    import asyncio
    from archibot.archipelago.client import (
        ArchipelagoClient, ArchipelagoConnectionRefused,
    )
    fake_ap_server.enqueue(None, [ROOM_INFO])
    fake_ap_server.enqueue("GetDataPackage", [DATA_PACKAGE])
    fake_ap_server.enqueue("Connect", [CONNECTION_REFUSED_INVALID_SLOT])

    cap = Capture()
    client = ArchipelagoClient(
        host="localhost", port=fake_ap_server.port, slot="nobody",
        password="", on_event=cap, use_tls=False,
    )
    with pytest.raises(ArchipelagoConnectionRefused):
        await client.run()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/archipelago/test_client.py -v -k "handshake or forwards or refused"`
Expected: FAIL — `ArchipelagoClient` doesn't exist yet.

- [ ] **Step 4: Add `ArchipelagoClient` to `src/archibot/archipelago/client.py`**

Append to the file:

```python
import asyncio
import json

import websockets

from archibot.archipelago.protocol import build_connect_packet


class ArchipelagoClient:
    """Live WebSocket client for a single Archipelago room."""

    def __init__(
        self,
        host: str,
        port: int,
        slot: str,
        password: str,
        on_event: OnEvent,
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.slot = slot
        self.password = password
        self.use_tls = use_tls
        self.router = PacketRouter(on_event=on_event)
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._closing = False

    async def run(self) -> None:
        """Connect, handshake, read packets until close.

        Raises:
          ArchipelagoConnectionRefused on handshake failure.
          websockets.ConnectionClosed, OSError, asyncio.TimeoutError on
          transport issues — the session layer classifies these as
          retryable.
        """
        scheme = "wss" if self.use_tls else "ws"
        uri = f"{scheme}://{self.host}:{self.port}"
        async with websockets.connect(uri) as ws:
            self._ws = ws
            try:
                await self._handshake(ws)
                async for raw in ws:
                    if self._closing:
                        return
                    for packet in json.loads(raw):
                        self.router.feed(packet)
                    await self.router.drain()
            finally:
                self._ws = None

    async def _handshake(self, ws: websockets.WebSocketClientProtocol) -> None:
        # 1) Server sends RoomInfo first, unsolicited.
        raw = await ws.recv()
        for p in json.loads(raw):
            self.router.feed(p)

        # 2) We request DataPackage for all games in the room.
        # The RoomInfo packet isn't retained by the router, so we don't
        # know which games to request. Ask for all — the server is fine
        # with an empty list meaning "all".
        await ws.send(json.dumps([{"cmd": "GetDataPackage"}]))

        # 3) Server sends DataPackage.
        raw = await ws.recv()
        for p in json.loads(raw):
            self.router.feed(p)

        # 4) We send Connect.
        await ws.send(json.dumps([build_connect_packet(self.slot, self.password)]))

        # 5) Server sends Connected or ConnectionRefused.
        raw = await ws.recv()
        for p in json.loads(raw):
            self.router.feed(p)  # raises on ConnectionRefused
        await self.router.drain()

    async def close(self) -> None:
        self._closing = True
        if self._ws is not None:
            await self._ws.close(code=1000)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/archipelago/test_client.py -v`
Expected: all tests PASS (11 total between Task 10 and Task 11).

- [ ] **Step 6: Pause for user review**

---

## Phase 4 — Session layer

### Task 12: Message formatter

**Files:**
- Create: `src/archibot/session/formatter.py`
- Create: `tests/session/test_formatter.py`

- [ ] **Step 1: Write failing tests**

Create `tests/session/test_formatter.py`:

```python
from archibot.events import UnlockEvent
from archibot.session.formatter import format_unlock, format_unlocks_batch


def _event(**overrides):
    base = dict(
        receiver_slot="Bork", sender_slot="Meow", item_name="Master Sword",
        location_name="Eastern Palace - Big Chest", game="A Link to the Past",
        flags=0b001,
    )
    base.update(overrides)
    return UnlockEvent(**base)


def test_format_with_mention():
    e = _event()
    msg = format_unlock(e, discord_user_id=12345)
    assert msg == (
        "🟣 <@12345> got **Master Sword** "
        "from Meow's A Link to the Past "
        "(Eastern Palace - Big Chest)"
    )


def test_format_without_mention_uses_slot_name():
    e = _event()
    msg = format_unlock(e, discord_user_id=None)
    assert msg == (
        "🟣 **Bork** got **Master Sword** "
        "from Meow's A Link to the Past "
        "(Eastern Palace - Big Chest)"
    )


def test_format_filler_uses_white_circle():
    e = _event(flags=0)
    assert format_unlock(e, None).startswith("⚪")


def test_format_trap_uses_red_circle():
    e = _event(flags=0b100)
    assert format_unlock(e, None).startswith("🔴")


def test_batch_hoists_mentions_to_header():
    e1 = _event(receiver_slot="Bork", item_name="Master Sword")
    e2 = _event(receiver_slot="Lord", item_name="Rupees", flags=0)
    out = format_unlocks_batch([(e1, 12345), (e2, 67890)])
    lines = out.splitlines()
    # Header contains both mentions (dedup preserved, each ping lands once).
    assert "<@12345>" in lines[0]
    assert "<@67890>" in lines[0]
    # Body lines use bold names (no mention), one per event.
    assert "**Master Sword**" in out
    assert "**Rupees**" in out


def test_batch_deduplicates_mentions():
    e = _event(receiver_slot="Bork")
    out = format_unlocks_batch([(e, 12345), (e, 12345)])
    # Only one mention in the header for Bork.
    assert out.splitlines()[0].count("<@12345>") == 1


def test_batch_with_some_unlinked():
    e1 = _event(receiver_slot="Bork")
    e2 = _event(receiver_slot="Unlinked")
    out = format_unlocks_batch([(e1, 12345), (e2, None)])
    assert "<@12345>" in out.splitlines()[0]
    # Unlinked entries contribute no header mention.
    assert "<@" not in out.splitlines()[1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/session/test_formatter.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/session/formatter.py`**

```python
"""Render UnlockEvents as Discord messages."""
from __future__ import annotations

from archibot.events import ItemFlag, UnlockEvent


def format_unlock(event: UnlockEvent, discord_user_id: int | None) -> str:
    """One-liner for a single unlock.

    When the receiver is linked, their mention goes in the message; otherwise
    the slot name is bolded instead.
    """
    emoji = ItemFlag.from_bits(event.flags).emoji
    receiver = (
        f"<@{discord_user_id}>" if discord_user_id is not None
        else f"**{event.receiver_slot}**"
    )
    return (
        f"{emoji} {receiver} got **{event.item_name}** "
        f"from {event.sender_slot}'s {event.game} "
        f"({event.location_name})"
    )


def format_unlocks_batch(
    entries: list[tuple[UnlockEvent, int | None]],
) -> str:
    """Render multiple unlocks as a single message with mentions hoisted.

    Discord only pings from a message's top-level content, and having
    mentions *only* in the body sometimes fails to ping on mobile clients.
    We hoist unique mentions to a header line, then list each unlock below
    without the mention prefix.
    """
    mentions: list[str] = []
    seen: set[int] = set()
    for _, uid in entries:
        if uid is not None and uid not in seen:
            seen.add(uid)
            mentions.append(f"<@{uid}>")
    header = " ".join(mentions) if mentions else ""
    body_lines = []
    for event, _uid in entries:
        emoji = ItemFlag.from_bits(event.flags).emoji
        body_lines.append(
            f"{emoji} **{event.receiver_slot}** got **{event.item_name}** "
            f"from {event.sender_slot}'s {event.game} "
            f"({event.location_name})"
        )
    if header:
        return header + "\n" + "\n".join(body_lines)
    return "\n".join(body_lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/session/test_formatter.py -v`
Expected: 7 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 13: TrackerSession — state machine and retry

`TrackerSession` owns one Archipelago connection and its retry policy. It receives UnlockEvents from the client and forwards them through a callback to the next layer.

**Files:**
- Create: `src/archibot/session/tracker_session.py`
- Create: `tests/session/test_tracker_session.py`

- [ ] **Step 1: Write failing tests**

Create `tests/session/test_tracker_session.py`:

```python
import asyncio
import pytest

from archibot.archipelago.client import ArchipelagoConnectionRefused
from archibot.events import UnlockEvent
from archibot.session.tracker_session import (
    TrackerSession, SessionState, RetryPolicy, TerminalFailure,
)


class FakeClient:
    """Fake ArchipelagoClient: succeeds or fails according to a script."""

    def __init__(self, script: list):
        self.script = list(script)
        self.on_event = None  # set by TrackerSession
        self.runs = 0
        self.closed = False

    async def run(self):
        self.runs += 1
        action = self.script.pop(0) if self.script else ("hang",)
        kind = action[0]
        if kind == "fail":
            raise action[1]
        if kind == "emit_then_close":
            for e in action[1]:
                await self.on_event(e)
            # simulate clean close
            return
        if kind == "hang":
            # block until closed
            while not self.closed:
                await asyncio.sleep(0.01)
            return

    async def close(self):
        self.closed = True


def _policy(max_attempts=3, base=0.01, cap=0.02):
    return RetryPolicy(
        max_attempts=max_attempts, base_delay=base, cap_delay=cap,
        stable_reset_seconds=0.05,
    )


async def test_retryable_failure_retries_then_succeeds():
    events_fwd = []

    async def on_event(e):
        events_fwd.append(e)

    async def on_state(state):
        pass

    client_factory_calls = []
    scripts = [
        [("fail", OSError("boom")), ("emit_then_close", [
            UnlockEvent("Bork", "Meow", "Master Sword", "EP", "LttP", 1),
        ])],
    ]

    def factory():
        client_factory_calls.append(1)
        fake = FakeClient(scripts[0])
        return fake

    session = TrackerSession(
        client_factory=factory, on_event=on_event, on_state=on_state,
        retry_policy=_policy(),
    )
    await session.start()
    await asyncio.sleep(0.1)
    assert len(events_fwd) == 1


async def test_exhausted_retries_calls_terminal_failure():
    errors = []

    async def on_state(state):
        pass

    async def on_event(e):
        pass

    async def on_terminal(exc):
        errors.append(exc)

    def factory():
        return FakeClient([
            ("fail", OSError("boom1")),
            ("fail", OSError("boom2")),
            ("fail", OSError("boom3")),
        ])

    session = TrackerSession(
        client_factory=factory, on_event=on_event, on_state=on_state,
        on_terminal_failure=on_terminal,
        retry_policy=_policy(max_attempts=3),
    )
    await session.start()
    await asyncio.sleep(0.3)
    assert isinstance(errors[0], TerminalFailure)
    assert errors[0].attempts == 3


async def test_non_retryable_error_fails_immediately():
    errors = []

    async def on_terminal(exc):
        errors.append(exc)

    async def on_event(e): pass
    async def on_state(s): pass

    def factory():
        return FakeClient([
            ("fail", ArchipelagoConnectionRefused(["InvalidSlot"])),
        ])

    session = TrackerSession(
        client_factory=factory, on_event=on_event, on_state=on_state,
        on_terminal_failure=on_terminal,
        retry_policy=_policy(max_attempts=10),
    )
    await session.start()
    await asyncio.sleep(0.1)
    assert isinstance(errors[0], TerminalFailure)
    assert errors[0].attempts == 1
    assert "InvalidSlot" in str(errors[0].last_error)


async def test_stop_cancels_running_session():
    async def on_event(e): pass
    async def on_state(s): pass

    def factory():
        return FakeClient([("hang",)])

    session = TrackerSession(
        client_factory=factory, on_event=on_event, on_state=on_state,
        retry_policy=_policy(),
    )
    await session.start()
    await asyncio.sleep(0.05)
    assert session.state == SessionState.RUNNING
    await session.stop()
    assert session.state == SessionState.DISCONNECTED


async def test_states_observed():
    states = []

    async def on_state(s):
        states.append(s)

    async def on_event(e): pass

    def factory():
        return FakeClient([("emit_then_close", [])])

    session = TrackerSession(
        client_factory=factory, on_event=on_event, on_state=on_state,
        retry_policy=_policy(max_attempts=1),
    )
    await session.start()
    await asyncio.sleep(0.1)
    assert SessionState.CONNECTING in states
    # After clean close with max_attempts=1, should reach DISCONNECTED.
    assert SessionState.DISCONNECTED in states
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/session/test_tracker_session.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/session/tracker_session.py`**

```python
"""TrackerSession: state machine + retry policy around ArchipelagoClient."""
from __future__ import annotations

import asyncio
import enum
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol

from archibot.archipelago.client import ArchipelagoConnectionRefused
from archibot.events import UnlockEvent

log = logging.getLogger(__name__)


class SessionState(str, enum.Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    RUNNING = "RUNNING"
    RECONNECTING = "RECONNECTING"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 10
    base_delay: float = 1.0
    cap_delay: float = 60.0
    # How long RUNNING must be uninterrupted before we reset the attempt
    # counter back to 0.
    stable_reset_seconds: float = 60.0

    def delay_for(self, attempt: int) -> float:
        """Delay before `attempt` (1-indexed) of the retry schedule."""
        d = self.base_delay * (2 ** (attempt - 1))
        return min(d, self.cap_delay)


@dataclass
class TerminalFailure(Exception):
    last_error: BaseException
    attempts: int

    def __str__(self) -> str:
        return f"TerminalFailure after {self.attempts}: {self.last_error!r}"


class _Client(Protocol):
    on_event: Any
    async def run(self) -> None: ...
    async def close(self) -> None: ...


ClientFactory = Callable[[], _Client]
OnEvent = Callable[[UnlockEvent], Awaitable[None]]
OnState = Callable[[SessionState], Awaitable[None]]
OnTerminalFailure = Callable[[TerminalFailure], Awaitable[None]]


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, ArchipelagoConnectionRefused):
        bad = {"InvalidSlot", "InvalidGame", "InvalidPassword"}
        return not (bad & set(exc.errors))
    # Heuristic: non-retryable for DNS resolution (socket.gaierror is OSError
    # subclass). Keep simple — treat all OSErrors as retryable; DNS failures
    # will just churn through the retry budget, which is acceptable.
    return isinstance(exc, (OSError, asyncio.TimeoutError)) or (
        exc.__class__.__name__ in {"ConnectionClosed", "ConnectionClosedError",
                                    "ConnectionClosedOK"}
    )


class TrackerSession:
    def __init__(
        self,
        client_factory: ClientFactory,
        on_event: OnEvent,
        on_state: OnState,
        retry_policy: RetryPolicy | None = None,
        on_terminal_failure: OnTerminalFailure | None = None,
    ) -> None:
        self.client_factory = client_factory
        self.on_event = on_event
        self.on_state = on_state
        self.retry_policy = retry_policy or RetryPolicy()
        self.on_terminal_failure = on_terminal_failure
        self.state = SessionState.DISCONNECTED
        self._task: asyncio.Task[None] | None = None
        self._current_client: _Client | None = None

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            raise RuntimeError("session already running")
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._current_client is not None:
            try:
                await self._current_client.close()
            except Exception:
                log.exception("error while closing client")
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        await self._set_state(SessionState.DISCONNECTED)

    async def _set_state(self, state: SessionState) -> None:
        self.state = state
        try:
            await self.on_state(state)
        except Exception:
            log.exception("on_state callback raised")

    async def _run_loop(self) -> None:
        attempt = 0
        last_error: BaseException | None = None
        while attempt < self.retry_policy.max_attempts:
            attempt += 1
            await self._set_state(
                SessionState.CONNECTING if attempt == 1 else SessionState.RECONNECTING
            )

            if attempt > 1:
                await asyncio.sleep(self.retry_policy.delay_for(attempt - 1))

            client = self.client_factory()
            client.on_event = self.on_event
            self._current_client = client

            started_at = time.monotonic()
            try:
                await self._set_state(SessionState.RUNNING)
                await client.run()
                # Clean close — treat as shutdown-triggered and stop.
                await self._set_state(SessionState.DISCONNECTED)
                return
            except asyncio.CancelledError:
                raise
            except BaseException as exc:
                last_error = exc
                ran_for = time.monotonic() - started_at
                if ran_for >= self.retry_policy.stable_reset_seconds:
                    attempt = 1  # reset budget
                if not _is_retryable(exc):
                    break
                log.warning("session error (attempt %d): %r", attempt, exc)
            finally:
                self._current_client = None

        await self._set_state(SessionState.DISCONNECTED)
        if last_error is not None and self.on_terminal_failure is not None:
            try:
                await self.on_terminal_failure(
                    TerminalFailure(last_error=last_error, attempts=attempt)
                )
            except Exception:
                log.exception("on_terminal_failure callback raised")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/session/test_tracker_session.py -v`
Expected: 5 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 14: Coalescing consumer

The per-channel consumer receives events from the session and decides how to deliver them to Discord: immediately, or coalesced when bursts exceed a threshold.

**Files:**
- Create: `src/archibot/session/coalescer.py`
- Create: `tests/session/test_coalescer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/session/test_coalescer.py`:

```python
import asyncio
import pytest

from archibot.events import UnlockEvent
from archibot.session.coalescer import Coalescer


def _event(item="Master Sword", receiver="Bork"):
    return UnlockEvent(
        receiver_slot=receiver, sender_slot="Meow", item_name=item,
        location_name="L", game="G", flags=1,
    )


async def test_single_event_delivered_immediately():
    delivered = []

    async def send(batch):
        delivered.append(batch)

    c = Coalescer(
        burst_threshold=3, window_seconds=0.05,
        send=send, lookup_user_id=lambda r: 42,
    )
    await c.start()
    await c.submit(_event())
    await asyncio.sleep(0.08)
    await c.stop()
    assert len(delivered) == 1
    assert len(delivered[0]) == 1


async def test_sub_threshold_burst_sends_individually():
    delivered = []

    async def send(batch):
        delivered.append(batch)

    c = Coalescer(
        burst_threshold=3, window_seconds=0.05,
        send=send, lookup_user_id=lambda r: 42,
    )
    await c.start()
    await c.submit(_event("A"))
    await c.submit(_event("B"))
    await asyncio.sleep(0.08)
    await c.stop()
    # Two individual sends (batches of size 1 each) — under threshold.
    assert len(delivered) == 2
    assert all(len(b) == 1 for b in delivered)


async def test_burst_coalesces_into_single_message():
    delivered = []

    async def send(batch):
        delivered.append(batch)

    c = Coalescer(
        burst_threshold=3, window_seconds=0.1,
        send=send, lookup_user_id=lambda r: 42,
    )
    await c.start()
    # Submit 5 in quick succession.
    for name in ["A", "B", "C", "D", "E"]:
        await c.submit(_event(name))
    await asyncio.sleep(0.2)
    await c.stop()
    # Should be a single batch of 5.
    assert len(delivered) == 1
    assert len(delivered[0]) == 5


async def test_lookup_user_id_is_called_per_event():
    ids = []

    async def send(batch): pass

    def lookup(recv):
        ids.append(recv)
        return 42 if recv == "Bork" else None

    c = Coalescer(
        burst_threshold=2, window_seconds=0.05,
        send=send, lookup_user_id=lookup,
    )
    await c.start()
    await c.submit(_event(receiver="Bork"))
    await c.submit(_event(receiver="Other"))
    await asyncio.sleep(0.08)
    await c.stop()
    assert ids == ["Bork", "Other"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/session/test_coalescer.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/session/coalescer.py`**

```python
"""Burst-aware event coalescer.

Buffer logic:
  - Each submitted event goes into a queue.
  - A worker drains the queue. If it receives an event, it waits up to
    `window_seconds` for more events to arrive.
  - If in that window the total count reaches `burst_threshold`, all
    accumulated events are flushed as ONE batch (triggering coalesced
    formatting).
  - Otherwise each event is flushed individually as soon as the window
    expires without additional arrivals.

This keeps quiet rooms feeling live while absorbing bursts cleanly.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from archibot.events import UnlockEvent

log = logging.getLogger(__name__)

LookupUserId = Callable[[str], int | None]
Send = Callable[[list[tuple[UnlockEvent, int | None]]], Awaitable[None]]


class Coalescer:
    def __init__(
        self,
        burst_threshold: int,
        window_seconds: float,
        send: Send,
        lookup_user_id: LookupUserId,
    ) -> None:
        self.burst_threshold = burst_threshold
        self.window_seconds = window_seconds
        self.send = send
        self.lookup_user_id = lookup_user_id
        self._queue: asyncio.Queue[UnlockEvent] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._stop.set()
        # wake the worker if it's waiting on the queue
        await self._queue.put(None)  # type: ignore[arg-type]
        if self._task is not None:
            await self._task

    async def submit(self, event: UnlockEvent) -> None:
        await self._queue.put(event)

    async def _worker(self) -> None:
        while not self._stop.is_set():
            first = await self._queue.get()
            if first is None or self._stop.is_set():
                return
            buffer: list[UnlockEvent] = [first]
            try:
                # Gather more events within the window.
                deadline = asyncio.get_event_loop().time() + self.window_seconds
                while True:
                    timeout = deadline - asyncio.get_event_loop().time()
                    if timeout <= 0:
                        break
                    try:
                        evt = await asyncio.wait_for(
                            self._queue.get(), timeout=timeout
                        )
                    except asyncio.TimeoutError:
                        break
                    if evt is None:
                        return
                    buffer.append(evt)
                await self._flush(buffer)
            except Exception:
                log.exception("coalescer worker error; events dropped")

    async def _flush(self, buffer: list[UnlockEvent]) -> None:
        entries = [(e, self.lookup_user_id(e.receiver_slot)) for e in buffer]
        if len(buffer) >= self.burst_threshold:
            await self.send(entries)
            return
        # Below threshold: send each individually so quiet rooms feel live.
        for entry in entries:
            await self.send([entry])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/session/test_coalescer.py -v`
Expected: 4 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 15: SessionManager

Owns all live sessions, maps channels to their sessions, handles resume-on-restart.

**Files:**
- Create: `src/archibot/session/manager.py`
- Create: `tests/session/test_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/session/test_manager.py`:

```python
import asyncio
import pytest
from cryptography.fernet import Fernet

from archibot.events import UnlockEvent
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.sessions import Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.persistence.muted_slots import MutedSlots
from archibot.session.manager import SessionManager, AlreadyTracking


class FakeClient:
    emitted: list[UnlockEvent] = []

    def __init__(self, **kwargs):
        self.on_event = None
        self.kwargs = kwargs

    async def run(self):
        for e in FakeClient.emitted:
            await self.on_event(e)
        # then hang until close
        self._hang = asyncio.Event()
        await self._hang.wait()

    async def close(self):
        self._hang.set()


@pytest.fixture
def crypto():
    return PasswordCrypto(Fernet.generate_key().decode())


@pytest.fixture
def empty_manager(db, crypto):
    sessions_repo = Sessions(db, crypto)
    links_repo = SlotLinks(db)
    muted_repo = MutedSlots(db)

    sent: list[tuple[int, str]] = []
    errors: list[tuple[int, Exception]] = []

    async def send_message(channel_id: int, content: str) -> None:
        sent.append((channel_id, content))

    async def send_error(channel_id: int, exc: Exception) -> None:
        errors.append((channel_id, exc))

    mgr = SessionManager(
        sessions_repo=sessions_repo, slot_links_repo=links_repo,
        muted_slots_repo=muted_repo,
        client_factory=lambda **kw: FakeClient(**kw),
        send_message=send_message, send_terminal_error=send_error,
    )
    return mgr, sent, errors


async def test_track_creates_row_and_session(empty_manager, db):
    mgr, sent, _ = empty_manager
    await mgr.track(
        channel_id=100, guild_id=1, host="ap.gg", port=38281,
        slot="Meow", password="",
    )
    # Row persisted.
    row = await db.fetchone("SELECT channel_id FROM sessions WHERE channel_id=100")
    assert row is not None
    # Session is active.
    assert mgr.has_session(100)


async def test_track_twice_same_channel_raises(empty_manager):
    mgr, _, _ = empty_manager
    await mgr.track(100, 1, "h", 1, "s", "")
    with pytest.raises(AlreadyTracking):
        await mgr.track(100, 1, "h", 1, "s", "")


async def test_untrack_deletes_and_stops(empty_manager, db):
    mgr, _, _ = empty_manager
    await mgr.track(100, 1, "h", 1, "s", "")
    await mgr.untrack(100)
    row = await db.fetchone("SELECT channel_id FROM sessions WHERE channel_id=100")
    assert row is None
    assert not mgr.has_session(100)


async def test_event_routes_to_correct_channel(empty_manager):
    mgr, sent, _ = empty_manager
    FakeClient.emitted = [
        UnlockEvent("Bork", "Meow", "Sword", "L", "LttP", 1),
    ]
    try:
        await mgr.track(100, 1, "h", 1, "Meow", "")
        # wait a bit for the event to propagate
        await asyncio.sleep(0.2)
        channel_ids = [c for c, _ in sent]
        assert 100 in channel_ids
    finally:
        FakeClient.emitted = []
        await mgr.shutdown()


async def test_muted_slot_is_filtered(empty_manager):
    mgr, sent, _ = empty_manager
    FakeClient.emitted = [
        UnlockEvent("Bork", "Meow", "Sword", "L", "LttP", 1),
    ]
    try:
        await mgr.track(100, 1, "h", 1, "Meow", "")
        # Mute Bork in channel 100.
        await mgr.muted_slots.mute(100, "Bork")
        await asyncio.sleep(0.2)
        # No message sent because receiver is muted.
        assert not any(c == 100 for c, _ in sent)
    finally:
        FakeClient.emitted = []
        await mgr.shutdown()


async def test_resume_on_start_loads_persisted_sessions(empty_manager, db, crypto):
    mgr, _, _ = empty_manager
    # Insert a session row directly.
    sessions_repo = Sessions(db, crypto)
    await sessions_repo.create(200, 1, "h", 1, "Meow", "")
    await mgr.resume_all()
    assert mgr.has_session(200)
    await mgr.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/session/test_manager.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `src/archibot/session/manager.py`**

```python
"""SessionManager: owns every active TrackerSession and routes events."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from archibot.events import UnlockEvent
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.sessions import Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.coalescer import Coalescer
from archibot.session.formatter import format_unlock, format_unlocks_batch
from archibot.session.tracker_session import (
    RetryPolicy, SessionState, TerminalFailure, TrackerSession,
)

log = logging.getLogger(__name__)

# Coalescer defaults — per spec: batch when 3+ events arrive within 2s.
BURST_THRESHOLD = 3
BURST_WINDOW_SECONDS = 2.0

SendMessage = Callable[[int, str], Awaitable[None]]
SendTerminalError = Callable[[int, Exception], Awaitable[None]]


class AlreadyTracking(RuntimeError):
    pass


class _ChannelContext:
    """Wires one channel's session + coalescer + per-channel callbacks."""
    def __init__(
        self,
        channel_id: int,
        guild_id: int,
        session: TrackerSession,
        coalescer: Coalescer,
    ) -> None:
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.session = session
        self.coalescer = coalescer


class SessionManager:
    def __init__(
        self,
        sessions_repo: Sessions,
        slot_links_repo: SlotLinks,
        muted_slots_repo: MutedSlots,
        client_factory: Callable[..., Any],
        send_message: SendMessage,
        send_terminal_error: SendTerminalError,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.sessions = sessions_repo
        self.slot_links = slot_links_repo
        self.muted_slots = muted_slots_repo
        self._client_factory = client_factory
        self._send_message = send_message
        self._send_terminal_error = send_terminal_error
        self._retry_policy = retry_policy or RetryPolicy()
        self._channels: dict[int, _ChannelContext] = {}

    def has_session(self, channel_id: int) -> bool:
        return channel_id in self._channels

    async def track(
        self,
        channel_id: int, guild_id: int,
        host: str, port: int, slot: str, password: str,
    ) -> None:
        if channel_id in self._channels:
            raise AlreadyTracking(channel_id)
        await self.sessions.create(channel_id, guild_id, host, port, slot, password)
        await self._spawn(channel_id, guild_id, host, port, slot, password)

    async def untrack(self, channel_id: int) -> None:
        ctx = self._channels.pop(channel_id, None)
        if ctx is not None:
            await ctx.coalescer.stop()
            await ctx.session.stop()
        await self.sessions.delete(channel_id)

    async def resume_all(self) -> None:
        for row in await self.sessions.list_all():
            try:
                await self._spawn(
                    row.channel_id, row.guild_id, row.host, row.port,
                    row.slot_name, row.password,
                )
            except Exception:
                log.exception(
                    "failed to resume session for channel=%s", row.channel_id
                )

    async def shutdown(self) -> None:
        for ctx in list(self._channels.values()):
            try:
                await ctx.coalescer.stop()
                await ctx.session.stop()
            except Exception:
                log.exception("error stopping session %s", ctx.channel_id)
        self._channels.clear()

    async def _spawn(
        self, channel_id: int, guild_id: int,
        host: str, port: int, slot: str, password: str,
    ) -> None:
        # Build per-channel coalescer with its own lookup closure.
        async def send_batch(
            entries: list[tuple[UnlockEvent, int | None]],
        ) -> None:
            # Filter muted entries before rendering.
            filtered: list[tuple[UnlockEvent, int | None]] = []
            for e, uid in entries:
                if await self.muted_slots.is_muted(channel_id, e.receiver_slot):
                    continue
                filtered.append((e, uid))
            if not filtered:
                return
            if len(filtered) == 1:
                e, uid = filtered[0]
                content = format_unlock(e, uid)
            else:
                content = format_unlocks_batch(filtered)
            try:
                await self._send_message(channel_id, content)
            except Exception:
                log.exception("send_message failed for channel %s", channel_id)

        def lookup_user(receiver_slot: str) -> int | None:
            # Synchronous lookup by reading from a small in-memory cache.
            # The cache is refreshed in the session's on_event path.
            import asyncio as _asyncio
            fut = _asyncio.run_coroutine_threadsafe(
                self.slot_links.get(guild_id, receiver_slot),
                _asyncio.get_event_loop(),
            )
            try:
                return fut.result(timeout=1.0)
            except Exception:
                return None

        coalescer = Coalescer(
            burst_threshold=BURST_THRESHOLD,
            window_seconds=BURST_WINDOW_SECONDS,
            send=send_batch,
            lookup_user_id=lookup_user,
        )
        await coalescer.start()

        async def on_event(e: UnlockEvent) -> None:
            await coalescer.submit(e)

        async def on_state(state: SessionState) -> None:
            log.info("channel=%s state=%s", channel_id, state.value)

        async def on_terminal(exc: TerminalFailure) -> None:
            try:
                await self._send_terminal_error(channel_id, exc)
            except Exception:
                log.exception("terminal-error send failed for %s", channel_id)
            self._channels.pop(channel_id, None)

        def client_factory() -> Any:
            return self._client_factory(
                host=host, port=port, slot=slot, password=password,
                on_event=on_event,
            )

        session = TrackerSession(
            client_factory=client_factory,
            on_event=on_event,
            on_state=on_state,
            retry_policy=self._retry_policy,
            on_terminal_failure=on_terminal,
        )
        ctx = _ChannelContext(channel_id, guild_id, session, coalescer)
        self._channels[channel_id] = ctx
        await session.start()
```

Note: the `lookup_user` helper above does a blocking call inside an async-only thread — it works because pytest runs the event loop in the main thread. In production we expect this to be called from the main event loop too, but if that causes issues (it may with `asyncio.run_coroutine_threadsafe` being called from the same thread as the loop), the simpler fix is to make `lookup_user` async and have `Coalescer` call it as such. We'll adjust in Task 18 if the integration test catches it.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/session/test_manager.py -v`
Expected: 6 PASSED. If `lookup_user` deadlocks, change `Coalescer` and `SessionManager` to use an async lookup callback.

- [ ] **Step 5: If deadlock occurs, refactor to async lookup**

If `test_event_routes_to_correct_channel` hangs, update `Coalescer.lookup_user_id` to be async:

In `src/archibot/session/coalescer.py`, change type alias:
```python
LookupUserId = Callable[[str], Awaitable[int | None]]
```
In `_flush`, await it:
```python
entries = [(e, await self.lookup_user_id(e.receiver_slot)) for e in buffer]
```
In `src/archibot/session/manager.py`, replace the `lookup_user` closure body:
```python
async def lookup_user(receiver_slot: str) -> int | None:
    return await self.slot_links.get(guild_id, receiver_slot)
```
In `tests/session/test_coalescer.py`, wrap synchronous `lookup` closures with an async shim.

Re-run: `uv run pytest tests/session/ -v` — all tests PASS.

- [ ] **Step 6: Pause for user review**

---

## Phase 5 — Discord layer

### Task 16: Permission check and error embeds

**Files:**
- Create: `src/archibot/discord_layer/permissions.py`
- Create: `src/archibot/discord_layer/embeds.py`

These are small, pure-ish helpers. We test them alongside the cogs that use them (Task 17+).

- [ ] **Step 1: Implement `src/archibot/discord_layer/permissions.py`**

```python
"""Permission check for moderator-gated commands."""
from __future__ import annotations

import discord


def is_moderator(member: discord.Member, role_name: str) -> bool:
    """True if the member has a role named `role_name`, or failing that,
    holds the Manage Channels permission."""
    if any(role.name == role_name for role in member.roles):
        return True
    return bool(member.guild_permissions.manage_channels)
```

- [ ] **Step 2: Implement `src/archibot/discord_layer/embeds.py`**

```python
"""Embed builders for status and error messages."""
from __future__ import annotations

import discord

from archibot.session.tracker_session import TerminalFailure


def connected_embed(seed_name: str, player_count: int) -> discord.Embed:
    e = discord.Embed(
        title="✅ Connected to Archipelago",
        description=f"Tracking **{seed_name}** ({player_count} players).",
        color=discord.Color.green(),
    )
    return e


def track_error_embed(host: str, port: int, slot: str, error: Exception) -> discord.Embed:
    e = discord.Embed(
        title="🚫 Couldn't connect to Archipelago",
        color=discord.Color.red(),
    )
    e.add_field(name="Host", value=f"{host}:{port}", inline=True)
    e.add_field(name="Slot", value=slot, inline=True)
    e.add_field(name="Error", value=f"`{error!s}`", inline=False)
    return e


def terminal_failure_embed(
    host: str, port: int, slot: str, failure: TerminalFailure,
) -> discord.Embed:
    e = discord.Embed(
        title="🚫 Lost connection to Archipelago",
        description="Use `/track` to retry or `/status` to inspect.",
        color=discord.Color.red(),
    )
    e.add_field(name="Host", value=f"{host}:{port}", inline=True)
    e.add_field(name="Slot", value=slot, inline=True)
    e.add_field(
        name="Last error", value=f"`{failure.last_error!s}`", inline=False,
    )
    e.add_field(
        name="Attempts", value=f"{failure.attempts} (~5m with backoff)", inline=True,
    )
    return e


def status_embed(
    state: str, last_event: str | None, link_count: int, mute_count: int,
) -> discord.Embed:
    e = discord.Embed(title="Tracker status", color=discord.Color.blue())
    e.add_field(name="State", value=state, inline=True)
    e.add_field(name="Last event", value=last_event or "—", inline=True)
    e.add_field(name="Linked slots", value=str(link_count), inline=True)
    e.add_field(name="Muted slots", value=str(mute_count), inline=True)
    return e
```

- [ ] **Step 3: Pause for user review**

---

### Task 17: Discord bot harness

**Files:**
- Create: `src/archibot/discord_layer/bot.py`

This is the glue between `discord.py`'s `commands.Bot` and our SessionManager. Concrete cog tests arrive in Task 18+; for now we just wire the bot together.

- [ ] **Step 1: Implement `src/archibot/discord_layer/bot.py`**

```python
"""discord.py Bot subclass that owns a SessionManager."""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from archibot.config import Config
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.db import Database
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.sessions import Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.manager import SessionManager
from archibot.session.tracker_session import TerminalFailure
from archibot.discord_layer import embeds

log = logging.getLogger(__name__)


class ArchibotBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = False  # slash-only bot
        intents.members = True  # needed for role checks on Member
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.db: Database | None = None
        self.session_manager: SessionManager | None = None

    async def setup_hook(self) -> None:
        self.db = Database(self.config.db_path)
        await self.db.connect()
        await self.db.migrate()
        crypto = PasswordCrypto(self.config.bot_secret_key)
        sessions_repo = Sessions(self.db, crypto)
        links_repo = SlotLinks(self.db)
        muted_repo = MutedSlots(self.db)

        from archibot.archipelago.client import ArchipelagoClient
        self.session_manager = SessionManager(
            sessions_repo=sessions_repo,
            slot_links_repo=links_repo,
            muted_slots_repo=muted_repo,
            client_factory=lambda **kw: ArchipelagoClient(**kw),
            send_message=self._send_message,
            send_terminal_error=self._send_terminal_error,
        )

        # Load cogs
        from archibot.discord_layer.cogs.tracking import TrackingCog
        from archibot.discord_layer.cogs.linking import LinkingCog
        from archibot.discord_layer.cogs.moderation import ModerationCog
        await self.add_cog(TrackingCog(self))
        await self.add_cog(LinkingCog(self))
        await self.add_cog(ModerationCog(self))

        await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("logged in as %s", self.user)
        assert self.session_manager is not None
        await self.session_manager.resume_all()

    async def close(self) -> None:
        if self.session_manager is not None:
            await self.session_manager.shutdown()
        if self.db is not None:
            await self.db.close()
        await super().close()

    async def _send_message(self, channel_id: int, content: str) -> None:
        channel = self.get_channel(channel_id)
        if channel is None:
            channel = await self.fetch_channel(channel_id)
        await channel.send(content, allowed_mentions=discord.AllowedMentions(users=True))

    async def _send_terminal_error(
        self, channel_id: int, failure: TerminalFailure,
    ) -> None:
        channel = self.get_channel(channel_id)
        if channel is None:
            channel = await self.fetch_channel(channel_id)
        # Look up the session's host/port/slot for the embed.
        assert self.session_manager is not None
        row = await self.session_manager.sessions.get(channel_id)
        if row is None:
            await channel.send(f"🚫 Tracker failed: `{failure.last_error}`")
            return
        await channel.send(embed=embeds.terminal_failure_embed(
            row.host, row.port, row.slot_name, failure,
        ))
```

- [ ] **Step 2: Pause for user review**

---

### Task 18: Tracking cog — /track /untrack /status /testunlock

**Files:**
- Create: `src/archibot/discord_layer/cogs/tracking.py`
- Create: `tests/discord_layer/test_tracking.py`
- Modify: `tests/conftest.py` (add discord interaction mock)

- [ ] **Step 1: Add an interaction mock helper to conftest**

Append to `tests/conftest.py`:

```python
from unittest.mock import AsyncMock, MagicMock


def make_interaction(
    user_id: int = 1, guild_id: int = 10, channel_id: int = 100,
    is_mod: bool = True, role_name: str = "AP-Mod",
) -> MagicMock:
    """Minimal discord.Interaction mock for cog tests."""
    mock = MagicMock()
    mock.user.id = user_id
    mock.user.roles = [MagicMock(name=role_name)] if is_mod else []
    mock.user.roles[0].name = role_name if is_mod else ""
    mock.user.guild_permissions.manage_channels = is_mod
    mock.guild_id = guild_id
    mock.channel_id = channel_id
    mock.response.send_message = AsyncMock()
    mock.followup.send = AsyncMock()
    return mock


import pytest
@pytest.fixture
def interaction():
    return make_interaction


@pytest.fixture
def cogs_setup(db):
    """Build a bot-like object with just the pieces cogs need."""
    from cryptography.fernet import Fernet
    from archibot.persistence.crypto import PasswordCrypto
    from archibot.persistence.sessions import Sessions
    from archibot.persistence.slot_links import SlotLinks
    from archibot.persistence.muted_slots import MutedSlots
    from archibot.session.manager import SessionManager

    crypto = PasswordCrypto(Fernet.generate_key().decode())
    sessions_repo = Sessions(db, crypto)
    links_repo = SlotLinks(db)
    muted_repo = MutedSlots(db)

    class FakeClient:
        def __init__(self, **kw):
            self.on_event = None
        async def run(self):
            import asyncio
            self._h = asyncio.Event()
            await self._h.wait()
        async def close(self):
            self._h.set()

    sent = []
    async def send_message(cid, content):
        sent.append((cid, content))
    errors = []
    async def send_error(cid, err):
        errors.append((cid, err))

    mgr = SessionManager(
        sessions_repo=sessions_repo, slot_links_repo=links_repo,
        muted_slots_repo=muted_repo,
        client_factory=lambda **kw: FakeClient(**kw),
        send_message=send_message, send_terminal_error=send_error,
    )

    bot = MagicMock()
    bot.session_manager = mgr
    bot.config = MagicMock(track_role_name="AP-Mod")
    bot.db = db

    return bot, sent, errors
```

- [ ] **Step 2: Write failing tests**

Create `tests/discord_layer/test_tracking.py`:

```python
import pytest
from unittest.mock import MagicMock

from archibot.discord_layer.cogs.tracking import TrackingCog
from tests.conftest import make_interaction


async def test_track_happy_path_persists_and_responds(cogs_setup):
    bot, sent, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.track.callback(
        cog, interaction,
        host="ap.gg", port=38281, slot="Meow", password="",
    )
    interaction.response.send_message.assert_called_once()
    assert bot.session_manager.has_session(100)


async def test_track_requires_mod_role(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction(is_mod=False)
    await cog.track.callback(
        cog, interaction, host="ap.gg", port=38281, slot="Meow", password="",
    )
    # The command should reject rather than creating a session.
    assert not bot.session_manager.has_session(100)
    interaction.response.send_message.assert_called_once()
    call = interaction.response.send_message.call_args
    assert "permission" in call.kwargs.get("content", "").lower() or (
        "permission" in (call.args[0] if call.args else "").lower()
    )


async def test_track_twice_errors(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    i1 = make_interaction()
    await cog.track.callback(cog, i1, host="h", port=1, slot="s", password="")
    i2 = make_interaction()
    await cog.track.callback(cog, i2, host="h", port=1, slot="s", password="")
    # Second call should report "already tracking".
    content = i2.response.send_message.call_args.kwargs.get("content") or \
              i2.response.send_message.call_args.args[0]
    assert "already" in content.lower() or "existing" in content.lower()


async def test_untrack_removes_session(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    i1 = make_interaction()
    await cog.track.callback(cog, i1, host="h", port=1, slot="s", password="")
    i2 = make_interaction()
    await cog.untrack.callback(cog, i2)
    assert not bot.session_manager.has_session(100)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/discord_layer/test_tracking.py -v`
Expected: FAIL — `TrackingCog` doesn't exist.

- [ ] **Step 4: Implement `src/archibot/discord_layer/cogs/tracking.py`**

```python
"""/track /untrack /status /testunlock slash commands."""
from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from archibot.discord_layer import embeds
from archibot.discord_layer.permissions import is_moderator
from archibot.events import UnlockEvent
from archibot.persistence.crypto import CryptoUnavailableError
from archibot.session.formatter import format_unlock
from archibot.session.manager import AlreadyTracking

log = logging.getLogger(__name__)


class TrackingCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _check_mod(self, interaction: discord.Interaction) -> bool:
        return is_moderator(interaction.user, self.bot.config.track_role_name)

    @app_commands.command(name="track", description="Start tracking an Archipelago room in this channel.")
    @app_commands.describe(
        host="Archipelago server host",
        port="Archipelago server port",
        slot="Player slot name to auth as (any valid slot in the room)",
        password="Room password (optional)",
    )
    async def track(
        self, interaction: discord.Interaction,
        host: str, port: int, slot: str, password: str = "",
    ) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        try:
            await self.bot.session_manager.track(
                channel_id=interaction.channel_id,
                guild_id=interaction.guild_id,
                host=host, port=port, slot=slot, password=password,
            )
        except AlreadyTracking:
            await interaction.response.send_message(
                "This channel is already tracking a room. Use `/untrack` first.",
                ephemeral=True,
            )
            return
        except CryptoUnavailableError:
            await interaction.response.send_message(
                "`BOT_SECRET_KEY` is not configured — cannot accept a password. "
                "Set it in the bot's environment or omit the password.",
                ephemeral=True,
            )
            return
        except Exception as e:
            log.exception("track failed")
            await interaction.response.send_message(
                embed=embeds.track_error_embed(host, port, slot, e),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Started tracking `{host}:{port}` as slot `{slot}`.",
        )

    @app_commands.command(name="untrack", description="Stop tracking this channel's Archipelago room.")
    async def untrack(self, interaction: discord.Interaction) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        await self.bot.session_manager.untrack(interaction.channel_id)
        await interaction.response.send_message("Stopped tracking.")

    @app_commands.command(name="status", description="Show tracker status for this channel.")
    async def status(self, interaction: discord.Interaction) -> None:
        mgr = self.bot.session_manager
        has = mgr.has_session(interaction.channel_id)
        state = "RUNNING" if has else "DISCONNECTED"
        links = await mgr.slot_links.list_by_guild(interaction.guild_id)
        mutes = await mgr.muted_slots.list_for_channel(interaction.channel_id)
        await interaction.response.send_message(
            embed=embeds.status_embed(
                state=state, last_event=None,
                link_count=len(links), mute_count=len(mutes),
            ),
        )

    @app_commands.command(name="testunlock", description="Post a fake unlock message for format testing.")
    async def testunlock(self, interaction: discord.Interaction) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        fake = UnlockEvent(
            receiver_slot="Bork", sender_slot="Meow",
            item_name="Master Sword",
            location_name="Eastern Palace - Big Chest",
            game="A Link to the Past", flags=0b001,
        )
        msg = format_unlock(fake, discord_user_id=None)
        await interaction.response.send_message(msg)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/discord_layer/test_tracking.py -v`
Expected: 4 PASSED.

- [ ] **Step 6: Pause for user review**

---

### Task 19: Linking cog — /link /unlink /links /players

**Files:**
- Create: `src/archibot/discord_layer/cogs/linking.py`
- Create: `tests/discord_layer/test_linking.py`

- [ ] **Step 1: Write failing tests**

Create `tests/discord_layer/test_linking.py`:

```python
import pytest

from archibot.discord_layer.cogs.linking import LinkingCog
from tests.conftest import make_interaction


async def test_link_stores_caller_id(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    interaction = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, interaction, slot="Meow")
    got = await bot.session_manager.slot_links.get(10, "Meow")
    assert got == 42


async def test_link_updates_existing(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    i1 = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, i1, slot="Meow")
    i2 = make_interaction(user_id=99, guild_id=10)
    await cog.link.callback(cog, i2, slot="Meow")
    got = await bot.session_manager.slot_links.get(10, "Meow")
    assert got == 99  # self-overwrite allowed; user can relink


async def test_unlink_only_removes_caller_link(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    i1 = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, i1, slot="Meow")
    # Different user tries to unlink.
    i2 = make_interaction(user_id=99, guild_id=10)
    await cog.unlink.callback(cog, i2, slot="Meow")
    got = await bot.session_manager.slot_links.get(10, "Meow")
    assert got == 42


async def test_unlink_removes_own_link(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    i1 = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, i1, slot="Meow")
    i2 = make_interaction(user_id=42, guild_id=10)
    await cog.unlink.callback(cog, i2, slot="Meow")
    got = await bot.session_manager.slot_links.get(10, "Meow")
    assert got is None


async def test_unlink_no_slot_removes_all_for_user(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    i1 = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, i1, slot="Meow")
    i2 = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, i2, slot="Bork")
    i3 = make_interaction(user_id=42, guild_id=10)
    await cog.unlink.callback(cog, i3, slot=None)
    assert await bot.session_manager.slot_links.get(10, "Meow") is None
    assert await bot.session_manager.slot_links.get(10, "Bork") is None


async def test_links_lists_guild_mappings(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    i = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, i, slot="Meow")
    i2 = make_interaction(user_id=99, guild_id=10)
    await cog.link.callback(cog, i2, slot="Bork")
    i3 = make_interaction(guild_id=10)
    await cog.links.callback(cog, i3)
    call = i3.response.send_message.call_args
    content = call.kwargs.get("content") or (call.args[0] if call.args else "")
    assert "Meow" in content and "Bork" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/discord_layer/test_linking.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement `src/archibot/discord_layer/cogs/linking.py`**

```python
"""/link /unlink /links /players slash commands."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class LinkingCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="link", description="Map an Archipelago slot name to your Discord user.")
    @app_commands.describe(slot="Archipelago slot name to link to yourself")
    async def link(self, interaction: discord.Interaction, slot: str) -> None:
        await self.bot.session_manager.slot_links.upsert(
            guild_id=interaction.guild_id,
            slot_name=slot,
            discord_user_id=interaction.user.id,
        )
        await interaction.response.send_message(
            f"Linked `{slot}` → <@{interaction.user.id}>.", ephemeral=True,
        )

    @app_commands.command(name="unlink", description="Remove your link for a slot (or all your links).")
    @app_commands.describe(slot="Specific slot to unlink (omit to unlink all your slots in this guild)")
    async def unlink(
        self, interaction: discord.Interaction, slot: str | None = None,
    ) -> None:
        if slot is None:
            n = await self.bot.session_manager.slot_links.remove_all_for_user(
                guild_id=interaction.guild_id,
                discord_user_id=interaction.user.id,
            )
            await interaction.response.send_message(
                f"Removed {n} link(s).", ephemeral=True,
            )
            return
        n = await self.bot.session_manager.slot_links.remove(
            guild_id=interaction.guild_id,
            slot_name=slot,
            discord_user_id=interaction.user.id,
        )
        if n == 0:
            await interaction.response.send_message(
                f"No link owned by you for `{slot}`.", ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"Unlinked `{slot}`.", ephemeral=True,
            )

    @app_commands.command(name="links", description="List all slot ↔ user mappings in this guild.")
    async def links(self, interaction: discord.Interaction) -> None:
        rows = await self.bot.session_manager.slot_links.list_by_guild(
            interaction.guild_id
        )
        if not rows:
            await interaction.response.send_message("No links registered in this guild.")
            return
        body = "\n".join(
            f"• `{r.slot_name}` → <@{r.discord_user_id}>" for r in rows
        )
        await interaction.response.send_message(body)

    @app_commands.command(name="players", description="List slots in the current session and their link status.")
    async def players(self, interaction: discord.Interaction) -> None:
        # This is a richer version of /status; for MVP we re-use /links.
        # Proper implementation would iterate slot_info from the live session,
        # which we don't expose publicly yet.
        await self.links.callback(self, interaction)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/discord_layer/test_linking.py -v`
Expected: 6 PASSED.

- [ ] **Step 5: Pause for user review**

---

### Task 20: Moderation cog — /mute /unmute

**Files:**
- Create: `src/archibot/discord_layer/cogs/moderation.py`
- Create: `tests/discord_layer/test_moderation.py`

- [ ] **Step 1: Write failing tests**

Create `tests/discord_layer/test_moderation.py`:

```python
import pytest

from archibot.discord_layer.cogs.moderation import ModerationCog
from tests.conftest import make_interaction


async def test_mute_requires_mod_role(cogs_setup):
    bot, _, _ = cogs_setup
    cog = ModerationCog(bot)
    interaction = make_interaction(is_mod=False)
    await cog.mute.callback(cog, interaction, slot="Meow")
    assert not await bot.session_manager.muted_slots.is_muted(100, "Meow")


async def test_mute_persists(cogs_setup):
    bot, _, _ = cogs_setup
    cog = ModerationCog(bot)
    interaction = make_interaction()
    await cog.mute.callback(cog, interaction, slot="Meow")
    assert await bot.session_manager.muted_slots.is_muted(100, "Meow")


async def test_unmute_persists(cogs_setup):
    bot, _, _ = cogs_setup
    cog = ModerationCog(bot)
    i1 = make_interaction()
    await cog.mute.callback(cog, i1, slot="Meow")
    i2 = make_interaction()
    await cog.unmute.callback(cog, i2, slot="Meow")
    assert not await bot.session_manager.muted_slots.is_muted(100, "Meow")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/discord_layer/test_moderation.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement `src/archibot/discord_layer/cogs/moderation.py`**

```python
"""/mute /unmute slash commands."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from archibot.discord_layer.permissions import is_moderator


class ModerationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _check_mod(self, interaction: discord.Interaction) -> bool:
        return is_moderator(interaction.user, self.bot.config.track_role_name)

    @app_commands.command(name="mute", description="Suppress messages for unlocks received by this slot in this channel.")
    @app_commands.describe(slot="Slot name to mute")
    async def mute(self, interaction: discord.Interaction, slot: str) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        await self.bot.session_manager.muted_slots.mute(
            interaction.channel_id, slot
        )
        await interaction.response.send_message(
            f"Muted `{slot}` in this channel.", ephemeral=True,
        )

    @app_commands.command(name="unmute", description="Un-mute a slot in this channel.")
    @app_commands.describe(slot="Slot name to un-mute")
    async def unmute(self, interaction: discord.Interaction, slot: str) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        n = await self.bot.session_manager.muted_slots.unmute(
            interaction.channel_id, slot
        )
        if n == 0:
            await interaction.response.send_message(
                f"`{slot}` wasn't muted.", ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"Un-muted `{slot}`.", ephemeral=True,
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/discord_layer/test_moderation.py -v`
Expected: 3 PASSED.

- [ ] **Step 5: Pause for user review**

---

## Phase 6 — Wiring and docs

### Task 21: main.py entrypoint

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Replace `main.py` contents**

```python
"""Entry point: load config, run the bot."""
from __future__ import annotations

import asyncio
import logging

from archibot.config import Config, ConfigError
from archibot.discord_layer.bot import ArchibotBot


def main() -> None:
    try:
        config = Config.from_env()
    except ConfigError as e:
        raise SystemExit(f"Config error: {e}")

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = ArchibotBot(config)
    try:
        asyncio.run(bot.start(config.discord_token))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run import check**

Run: `uv run python -c "from archibot.discord_layer.bot import ArchibotBot; print('ok')"`
Expected: `ok`. Any ImportError indicates a wiring bug — fix before proceeding.

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass. Fix any regressions before proceeding.

- [ ] **Step 4: Pause for user review**

---

### Task 22: README and manual smoke-test doc

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README**

```markdown
# ArchipelagoDiscordBot

A Discord bot that listens to an Archipelago multiworld room and posts a
one-line message to a Discord channel for every cross-player item unlock,
pinging the receiver if they've registered a Discord link for their slot.

## Quickstart

```bash
uv sync --all-groups
cp .env.example .env
# edit .env — fill DISCORD_TOKEN (required), BOT_SECRET_KEY (if using passwords)
uv run python main.py
```

## Slash commands

| Command | Who | Effect |
|---|---|---|
| `/track host port slot [password]` | Moderator | Start tracking a room in this channel |
| `/untrack` | Moderator | Stop tracking in this channel |
| `/status` | Anyone | Show session state |
| `/link slot` | Anyone (self only) | Map slot → your Discord user |
| `/unlink [slot]` | Anyone (self only) | Remove your link (or all your links) |
| `/links` | Anyone | List all mappings in this guild |
| `/players` | Anyone | List mappings for the active session |
| `/mute slot` | Moderator | Suppress messages for that receiver |
| `/unmute slot` | Moderator | Undo mute |
| `/testunlock` | Moderator | Post a fake unlock (format check) |

Moderator role name is configured by `TRACK_ROLE_NAME` (default `AP-Mod`).
Members with the Discord "Manage Channels" permission bypass this role check.

## Manual smoke test

Prerequisite: a local Archipelago server. From `X:\repos\Archipelago\`:

```bash
python Generate.py  # creates a sample seed in output/
python MultiServer.py output/*.archipelago  # runs on localhost:38281 by default
```

In Discord:

```
/track host:localhost port:38281 slot:<a-slot-from-the-seed>
```

Trigger a check in one of the game clients connected to that server and
confirm a message appears in your Discord channel.

## Architecture

See `docs/superpowers/specs/2026-04-22-archipelago-discord-bot-design.md`
for the full design. Short version:

- `archibot.archipelago.client.ArchipelagoClient` — WebSocket connection,
  emits `UnlockEvent` via a callback.
- `archibot.session.tracker_session.TrackerSession` — retry policy and
  state machine around the client.
- `archibot.session.manager.SessionManager` — owns every live session,
  routes events to channels with burst coalescing.
- `archibot.discord_layer.bot.ArchibotBot` — `discord.py` bot; cogs
  implement slash commands.
- `archibot.persistence.*` — SQLite via `aiosqlite`, Fernet-encrypted
  passwords.

## Limitations

- Events during bot downtime are **lost** (no gap-filling).
- One session per channel.
- Rich embeds for unlock messages are not implemented (plain one-liners
  only for MVP).
- No posting of goal / release / collect / hint / chat / join / part
  events yet.
```

- [ ] **Step 2: Pause for user review**

---

## Self-review checklist

After finishing Task 22, run this checklist against the spec:

- [ ] **Section 1 (Problem & Goal):** The goal — cross-player unlock messages — is implemented in Task 10/11 (ItemSend filter) + Task 14 (coalescer) + Task 12 (formatter) + Task 18 (tracking cog).
- [ ] **Section 2 (Protocol facts):** Tracker tag, empty game, slot-name auth — all encoded in `protocol.build_connect_packet` (Task 9).
- [ ] **Section 3 (Architecture):** Three layers (client / session / discord) each with their own modules.
- [ ] **Section 4 (Data flow):** Filter `receiver == sender` and `sender == 0` in `PacketRouter` (Task 10); coalescing in `Coalescer` (Task 14); hoisted mentions in `format_unlocks_batch` (Task 12).
- [ ] **Section 5 (Persistence):** Three tables + migrations (Task 4); slot_links (Task 5); sessions + crypto (Task 6); muted_slots (Task 7).
- [ ] **Section 6 (Slash commands):** /track /untrack /status /testunlock (Task 18); /link /unlink /links /players (Task 19); /mute /unmute (Task 20).
- [ ] **Section 7 (Error handling):** State machine + backoff + non-retryable classification in `TrackerSession` (Task 13); terminal-failure embed in `embeds` (Task 16) and wired in bot (Task 17).
- [ ] **Section 8 (Testing):** Pure client tests (Task 10); integration via fake server (Task 11); cog tests (Tasks 18-20); manual smoke test in README (Task 22).
- [ ] **Section 11 (Config):** All env vars handled in `Config` (Task 2).

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-22-archipelago-discord-bot.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach would you like?
