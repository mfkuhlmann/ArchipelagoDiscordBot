"""/track, /untrack, /status, and /testunlock."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from archibot.discord_layer import embeds
from archibot.discord_layer.permissions import is_moderator
from archibot.events import UnlockEvent
from archibot.persistence.crypto import CryptoUnavailableError
from archibot.session.formatter import format_unlock


class TrackingCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _check_mod(self, interaction: discord.Interaction) -> bool:
        return is_moderator(interaction.user, self.bot.config.track_role_name)

    @app_commands.command(name="track", description="Track an Archipelago room in this channel.")
    async def track(
        self,
        interaction: discord.Interaction,
        host: str,
        port: int,
        slot: str,
        password: str = "",
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
                host=host,
                port=port,
                slot_name=slot,
                password=password,
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        except CryptoUnavailableError:
            await interaction.response.send_message(
                "This bot does not have a BOT_SECRET_KEY configured and cannot accept a password. "
                "Set it in the bot's environment or omit the password.",
                ephemeral=True,
            )
            return
        except Exception as exc:
            await interaction.response.send_message(
                embed=embeds.track_error_embed(host, port, slot, exc),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Started tracking `{host}:{port}` as slot `{slot}`."
        )

    @app_commands.command(name="untrack", description="Stop tracking in this channel.")
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
        manager = self.bot.session_manager
        links = await manager.slot_links.list_by_guild(interaction.guild_id)
        mutes = await manager.muted_slots.list_for_channel(interaction.channel_id)
        await interaction.response.send_message(
            embed=embeds.status_embed(
                state=manager.state_for_channel(interaction.channel_id),
                last_event=None,
                link_count=len(links),
                mute_count=len(mutes),
            )
        )

    @app_commands.command(name="testunlock", description="Post a fake unlock message.")
    async def testunlock(self, interaction: discord.Interaction) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        event = UnlockEvent(
            receiver_slot="Bork",
            sender_slot="Meow",
            item_name="Master Sword",
            location_name="Eastern Palace - Big Chest",
            game="A Link to the Past",
            flags=0b001,
        )
        await interaction.response.send_message(format_unlock(event, None))
