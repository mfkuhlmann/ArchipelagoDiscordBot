from archibot.events import UnlockEvent
from archibot.session.formatter import format_unlock, format_unlocks_batch


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


def test_format_unlock_batch_hoists_mentions():
    text = format_unlocks_batch([(make_event("Bork"), 123), (make_event("Zed"), 456)])
    assert text.splitlines()[0] == "<@123> <@456>"
    assert "Bork" in text
    assert "Zed" in text
