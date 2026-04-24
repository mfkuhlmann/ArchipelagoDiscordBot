from cryptography.fernet import Fernet

import pytest

from archibot.persistence.crypto import CryptoUnavailableError, PasswordCrypto
from archibot.persistence.sessions import Sessions


async def test_upsert_and_get_passwordless_session(db):
    repo = Sessions(db, PasswordCrypto(None))
    await repo.upsert(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
        password="",
    )
    stored = await repo.get(100)
    assert stored is not None
    record, password = stored
    assert record.host == "localhost"
    assert record.message_style == "embed"
    assert record.room_seed_name is None
    assert password == ""


async def test_upsert_encrypts_and_decrypts_password(db):
    repo = Sessions(db, PasswordCrypto(Fernet.generate_key().decode()))
    await repo.upsert(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="plain",
        password="hunter2",
    )
    record, password = await repo.get(100)
    assert record.message_style == "plain"
    assert password == "hunter2"


async def test_password_requires_key(db):
    repo = Sessions(db, PasswordCrypto(None))
    with pytest.raises(CryptoUnavailableError):
        await repo.upsert(
            channel_id=100,
            guild_id=10,
            host="localhost",
            port=38281,
            slot_name="Meow",
            message_style="embed",
            password="hunter2",
        )


async def test_delete_removes_row(db):
    repo = Sessions(db, PasswordCrypto(None))
    await repo.upsert(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
        password="",
    )
    assert await repo.delete(100) == 1
    assert await repo.get(100) is None


async def test_update_room_seed_name(db):
    repo = Sessions(db, PasswordCrypto(None))
    await repo.upsert(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        message_style="embed",
        password="",
    )
    await repo.update_room_seed_name(100, "Sample Seed")
    record, _ = await repo.get(100)
    assert record.room_seed_name == "Sample Seed"
