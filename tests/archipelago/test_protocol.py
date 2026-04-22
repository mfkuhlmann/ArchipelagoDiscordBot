from archibot.archipelago.protocol import (
    PROGRESSION,
    TRACKER_TAG,
    build_connect_packet,
    emoji_for_flags,
    lookup_item_name,
    lookup_location_name,
    normalize_data_package,
    normalize_slot_info,
    slot_name,
)
from tests.fixtures.ap_frames import DEFAULT_DATA_PACKAGE, DEFAULT_SLOT_INFO


def test_build_connect_packet_uses_tracker_tag():
    packet = build_connect_packet("Meow", "pw")
    assert packet["name"] == "Meow"
    assert packet["password"] == "pw"
    assert TRACKER_TAG in packet["tags"]
    assert packet["game"] == ""


def test_lookup_helpers_resolve_names():
    data_package = normalize_data_package(DEFAULT_DATA_PACKAGE)
    assert lookup_item_name(data_package, "A Link to the Past", 1) == "Lamp"
    assert lookup_item_name(data_package, "Super Metroid", 1) == "Missile"
    assert (
        lookup_location_name(data_package, "A Link to the Past", 10)
        == "Eastern Palace - Big Chest"
    )


def test_slot_name_falls_back_to_slot_marker():
    slots = normalize_slot_info(DEFAULT_SLOT_INFO)
    assert slot_name(slots, 1) == "Meow"
    assert slot_name(slots, 999) == "slot[999]"


def test_emoji_for_flags_prioritizes_progression():
    assert emoji_for_flags(PROGRESSION) == "🟣"
