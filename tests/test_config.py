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
