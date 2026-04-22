"""/mute and /unmute."""
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

    @app_commands.command(name="mute", description="Mute a slot for this channel.")
    async def mute(self, interaction: discord.Interaction, slot: str) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        await self.bot.session_manager.muted_slots.mute(interaction.channel_id, slot)
        await interaction.response.send_message(f"Muted `{slot}` in this channel.", ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a slot for this channel.")
    async def unmute(self, interaction: discord.Interaction, slot: str) -> None:
        if not self._check_mod(interaction):
            await interaction.response.send_message(
                "You need the moderator role to use this command.",
                ephemeral=True,
            )
            return
        removed = await self.bot.session_manager.muted_slots.unmute(interaction.channel_id, slot)
        if removed:
            await interaction.response.send_message(f"Un-muted `{slot}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"`{slot}` wasn't muted.", ephemeral=True)
