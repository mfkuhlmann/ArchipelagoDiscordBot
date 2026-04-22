"""Password encryption helpers."""
from __future__ import annotations

from cryptography.fernet import Fernet


class CryptoUnavailableError(RuntimeError):
    """Raised when password encryption is unavailable."""


class PasswordCrypto:
    def __init__(self, key: str | None) -> None:
        if key is None:
            self._fernet: Fernet | None = None
        else:
            self._fernet = Fernet(key.encode("utf-8"))

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
