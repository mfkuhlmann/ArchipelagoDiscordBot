import discord

from archibot.events import UnlockEvent
from archibot.session.formatter import (
    color_for_flags,
    format_unlock,
    format_unlocks_batch,
    unlock_embed,
)


def make_event(receiver: str = "Bork") -> UnlockEvent:
    return UnlockEvent(
        receiver_slot=receiver,
        sender_slot="Meow",
        item_name="Master Sword",
        location_name="Eastern Palace - Big Chest",
        game="A Link to the Past",
        flags=1,
    )


def test_format_unlock_uses_mention_when_available():
    text = format_unlock(make_event(), 123)
    assert "<@123>" in text
    assert "**Master Sword**" in text


def test_unlock_embed_uses_color_and_location():
    embed = unlock_embed(make_event(), 123)
    assert embed.title == "🟣 Master Sword"
    assert embed.description == "Bork got an item from Meow's A Link to the Past"
    assert embed.fields[0].value == "Eastern Palace - Big Chest"
    assert embed.color == discord.Color.purple()


def test_format_unlock_batch_hoists_mentions_into_content_and_embed():
    content, embed = format_unlocks_batch([(make_event("Bork"), 123), (make_event("Zed"), 456)])
    assert content == "<@123> <@456>"
    assert embed.title == "2 unlocks"
    assert "Bork" in embed.description
    assert "Zed" in embed.description


def test_color_for_flags_uses_circle_mapping():
    assert color_for_flags(0b001) == discord.Color.purple()
    assert color_for_flags(0b010) == discord.Color.blue()
    assert color_for_flags(0b100) == discord.Color.red()
