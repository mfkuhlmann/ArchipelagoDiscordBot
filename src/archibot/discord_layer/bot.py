"""Discord bot harness."""
from __future__ import annotations

import discord
from discord.ext import commands

from archibot.config import Config
from archibot.discord_layer import embeds
from archibot.discord_layer.cogs.linking import LinkingCog
from archibot.discord_layer.cogs.moderation import ModerationCog
from archibot.discord_layer.cogs.tracking import TrackingCog
from archibot.persistence.crypto import PasswordCrypto
from archibot.persistence.db import Database
from archibot.persistence.muted_slots import MutedSlots
from archibot.persistence.sessions import SessionRecord, Sessions
from archibot.persistence.slot_links import SlotLinks
from archibot.session.manager import SessionManager


class ArchibotBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.db = Database(config.db_path)
        self.password_crypto = PasswordCrypto(config.bot_secret_key)
        self.session_manager: SessionManager | None = None

    async def setup_hook(self) -> None:
        await self.db.connect()
        await self.db.migrate()
        slot_links = SlotLinks(self.db)
        sessions = Sessions(self.db, self.password_crypto)
        muted_slots = MutedSlots(self.db)
        self.session_manager = SessionManager(
            slot_links=slot_links,
            sessions=sessions,
            muted_slots=muted_slots,
            password_crypto=self.password_crypto,
            post_message=self._post_message,
            post_failure=self._post_failure,
        )
        await self.add_cog(TrackingCog(self))
        await self.add_cog(LinkingCog(self))
        await self.add_cog(ModerationCog(self))
        await self.session_manager.restore_sessions()

    async def close(self) -> None:
        if self.session_manager is not None:
            await self.session_manager.close()
        await self.db.close()
        await super().close()

    async def _post_message(
        self,
        *,
        channel_id: int,
        content: str | None = None,
        embed: discord.Embed | None = None,
    ) -> None:
        channel = self.get_channel(channel_id)
        if channel is None:
            channel = await self.fetch_channel(channel_id)
        await channel.send(content=content, embed=embed)

    async def _post_failure(
        self,
        channel_id: int,
        record: SessionRecord,
        error: Exception,
        attempts: int,
    ) -> None:
        await self._post_message(
            channel_id=channel_id,
            embed=embeds.terminal_failure_embed(record, error, attempts),
        )
