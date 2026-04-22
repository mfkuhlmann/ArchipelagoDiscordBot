"""/link, /unlink, /links, and /players."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class LinkingCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="link", description="Link a slot to yourself.")
    async def link(self, interaction: discord.Interaction, slot: str) -> None:
        await self.bot.session_manager.slot_links.upsert(
            guild_id=interaction.guild_id,
            slot_name=slot,
            discord_user_id=interaction.user.id,
        )
        await interaction.response.send_message(
            f"Linked `{slot}` -> <@{interaction.user.id}>.",
            ephemeral=True,
        )

    @app_commands.command(name="unlink", description="Remove one or all of your links.")
    async def unlink(
        self,
        interaction: discord.Interaction,
        slot: str | None = None,
    ) -> None:
        if slot is None:
            removed = await self.bot.session_manager.slot_links.remove_all_for_user(
                interaction.guild_id,
                interaction.user.id,
            )
            await interaction.response.send_message(
                f"Removed {removed} link(s).",
                ephemeral=True,
            )
            return

        removed = await self.bot.session_manager.slot_links.remove(
            guild_id=interaction.guild_id,
            slot_name=slot,
            discord_user_id=interaction.user.id,
        )
        if removed:
            await interaction.response.send_message(f"Unlinked `{slot}`.", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"No link owned by you for `{slot}`.",
                ephemeral=True,
            )

    @app_commands.command(name="links", description="List slot links in this guild.")
    async def links(self, interaction: discord.Interaction) -> None:
        rows = await self.bot.session_manager.slot_links.list_by_guild(interaction.guild_id)
        if not rows:
            await interaction.response.send_message("No links registered in this guild.")
            return
        body = "\n".join(f"• `{row.slot_name}` -> <@{row.discord_user_id}>" for row in rows)
        await interaction.response.send_message(body)

    @app_commands.command(name="players", description="List slots for the active session.")
    async def players(self, interaction: discord.Interaction) -> None:
        players = self.bot.session_manager.players_for_channel(interaction.channel_id)
        if not players:
            await interaction.response.send_message("No active session in this channel.")
            return
        links = {
            row.slot_name: row.discord_user_id
            for row in await self.bot.session_manager.slot_links.list_by_guild(interaction.guild_id)
        }
        muted = set(await self.bot.session_manager.muted_slots.list_for_channel(interaction.channel_id))
        lines = []
        for player in players:
            status = "[muted]" if player in muted else "[linked]" if player in links else "[unlinked]"
            lines.append(f"{status} `{player}`")
        await interaction.response.send_message("\n".join(lines))
