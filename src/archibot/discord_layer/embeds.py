"""Embeds used by the bot for status and errors."""
from __future__ import annotations

import discord

from archibot.persistence.raspberry_counts import RaspberryCount
from archibot.persistence.sessions import SessionRecord


def track_error_embed(host: str, port: int, slot: str, error: Exception) -> discord.Embed:
    embed = discord.Embed(title="Unable to start tracking", color=discord.Color.red())
    embed.add_field(name="Host", value=f"{host}:{port}", inline=False)
    embed.add_field(name="Slot", value=slot, inline=False)
    embed.add_field(name="Error", value=str(error) or type(error).__name__, inline=False)
    return embed


def status_embed(
    *,
    state: str,
    last_event: str | None,
    link_count: int,
    mute_count: int,
) -> discord.Embed:
    embed = discord.Embed(title="Archipelago Tracker Status")
    embed.add_field(name="State", value=state, inline=False)
    embed.add_field(name="Last event", value=last_event or "Never", inline=False)
    embed.add_field(name="Linked slots", value=str(link_count), inline=True)
    embed.add_field(name="Muted slots", value=str(mute_count), inline=True)
    return embed


def terminal_failure_embed(
    record: SessionRecord,
    error: Exception,
    attempts: int,
) -> discord.Embed:
    embed = discord.Embed(
        title="Lost connection to Archipelago",
        description="Use /track to retry or /status to inspect.",
        color=discord.Color.red(),
    )
    embed.add_field(name="Host", value=f"{record.host}:{record.port}", inline=False)
    embed.add_field(name="Slot", value=record.slot_name, inline=False)
    embed.add_field(name="Last error", value=type(error).__name__, inline=False)
    embed.add_field(name="Attempts made", value=str(attempts), inline=False)
    return embed


def raspberry_embed(total: int, counts: list[RaspberryCount]) -> discord.Embed:
    embed = discord.Embed(title="Raspberry Counter", color=discord.Color.magenta())
    embed.add_field(name="Total found", value=str(total), inline=False)
    if counts:
        body = "\n".join(f"{row.sender_slot}: {row.count}" for row in counts)
    else:
        body = "No Raspberries found yet."
    embed.add_field(name="Found by player", value=body, inline=False)
    return embed
