"""Unlock message formatting helpers."""
from __future__ import annotations

from collections.abc import Iterable

from archibot.archipelago.protocol import emoji_for_flags
from archibot.events import UnlockEvent


def format_unlock(event: UnlockEvent, discord_user_id: int | None) -> str:
    receiver = f"<@{discord_user_id}>" if discord_user_id is not None else event.receiver_slot
    return (
        f"{emoji_for_flags(event.flags)} {receiver} got **{event.item_name}** from "
        f"{event.sender_slot}'s {event.game} ({event.location_name})"
    )


def format_unlocks_batch(
    entries: Iterable[tuple[UnlockEvent, int | None]],
) -> str:
    rows = list(entries)
    mentions = sorted({f"<@{user_id}>" for _, user_id in rows if user_id is not None})
    header = " ".join(mentions)
    lines = [format_unlock(event, None) for event, _ in rows]
    if header:
        return header + "\n" + "\n".join(lines)
    return "\n".join(lines)
