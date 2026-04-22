"""Environment-backed configuration for the bot."""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


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
