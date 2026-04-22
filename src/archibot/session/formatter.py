"""Unlock message formatting helpers."""
from __future__ import annotations

from collections.abc import Iterable

import discord

from archibot.archipelago.protocol import emoji_for_flags
from archibot.events import UnlockEvent


def mention_for_user(discord_user_id: int | None) -> str | None:
    if discord_user_id is None:
        return None
    return f"<@{discord_user_id}>"


def color_for_flags(flags: int) -> discord.Color:
    emoji = emoji_for_flags(flags)
    if emoji == "🔴":
        return discord.Color.red()
    if emoji == "🟣":
        return discord.Color.purple()
    if emoji == "🔵":
        return discord.Color.blue()
    return discord.Color.light_grey()


def format_unlock(event: UnlockEvent, discord_user_id: int | None) -> str:
    receiver = mention_for_user(discord_user_id) or event.receiver_slot
    return (
        f"{emoji_for_flags(event.flags)} {receiver} got **{event.item_name}** from "
        f"{event.sender_slot}'s {event.game} ({event.location_name})"
    )


def unlock_embed(event: UnlockEvent, discord_user_id: int | None) -> discord.Embed:
    embed = discord.Embed(
        title=f"{emoji_for_flags(event.flags)} {event.item_name}",
        description=f"{event.receiver_slot} got an item from {event.sender_slot}'s {event.game}",
        color=color_for_flags(event.flags),
    )
    embed.add_field(name="Location", value=event.location_name, inline=False)
    return embed


def format_unlocks_batch(
    entries: Iterable[tuple[UnlockEvent, int | None]],
) -> tuple[str | None, discord.Embed]:
    rows = list(entries)
    mentions = sorted({mention for _, user_id in rows if (mention := mention_for_user(user_id))})
    lines = [format_unlock(event, None) for event, _ in rows]
    max_flags = max((event.flags for event, _ in rows), default=0)
    embed = discord.Embed(
        title=f"{len(rows)} unlocks",
        description="\n".join(lines),
        color=color_for_flags(max_flags),
    )
    content = " ".join(mentions) if mentions else None
    return content, embed
