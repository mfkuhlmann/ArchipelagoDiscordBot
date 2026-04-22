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
        password="",
    )
    stored = await repo.get(100)
    assert stored is not None
    record, password = stored
    assert record.host == "localhost"
    assert password == ""


async def test_upsert_encrypts_and_decrypts_password(db):
    repo = Sessions(db, PasswordCrypto(Fernet.generate_key().decode()))
    await repo.upsert(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
        password="hunter2",
    )
    _, password = await repo.get(100)
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
        password="",
    )
    assert await repo.delete(100) == 1
    assert await repo.get(100) is None
