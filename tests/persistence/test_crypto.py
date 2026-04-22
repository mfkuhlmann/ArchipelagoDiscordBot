import pytest
from cryptography.fernet import Fernet

from archibot.persistence.crypto import CryptoUnavailableError, PasswordCrypto


def test_roundtrip_encrypts_and_decrypts():
    key = Fernet.generate_key().decode()
    crypto = PasswordCrypto(key)
    ciphertext = crypto.encrypt("hunter2")
    assert ciphertext != b"hunter2"
    assert crypto.decrypt(ciphertext) == "hunter2"


def test_missing_key_raises_on_encrypt():
    crypto = PasswordCrypto(None)
    with pytest.raises(CryptoUnavailableError):
        crypto.encrypt("hunter2")


def test_missing_key_raises_on_decrypt():
    crypto = PasswordCrypto(None)
    with pytest.raises(CryptoUnavailableError):
        crypto.decrypt(b"anything")


def test_empty_password_roundtrips_without_key():
    crypto = PasswordCrypto(None)
    assert crypto.encrypt("") is None
    assert crypto.decrypt(None) == ""


def test_invalid_key_raises():
    with pytest.raises(ValueError):
        PasswordCrypto("not-a-valid-fernet-key")
