"""Entry point: load config and run the bot."""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from archibot.config import Config, ConfigError
from archibot.discord_layer.bot import ArchibotBot


def main() -> None:
    try:
        config = Config.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Config error: {exc}") from exc

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
