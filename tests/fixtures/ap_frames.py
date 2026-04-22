"""Recorded-ish AP protocol frames used in tests."""
from __future__ import annotations

import json


DEFAULT_SLOT_INFO = {
    1: {"name": "Meow", "game": "A Link to the Past"},
    2: {"name": "Bork", "game": "Super Metroid"},
    3: {"name": "Zed", "game": "A Link to the Past"},
}

DEFAULT_DATA_PACKAGE = {
    "games": {
        "A Link to the Past": {
            "item_name_to_id": {"Master Sword": 1},
            "location_name_to_id": {"Eastern Palace - Big Chest": 10},
        },
        "Super Metroid": {
            "item_name_to_id": {"Missile": 2},
            "location_name_to_id": {"Landing Site": 20},
        },
    }
}


def room_info(seed_name: str = "Sample Seed") -> str:
    return json.dumps([{"cmd": "RoomInfo", "seed_name": seed_name}])


def connected(slot_info=None) -> str:
    payload = slot_info or DEFAULT_SLOT_INFO
    normalized = {str(key): value for key, value in payload.items()}
    return json.dumps([{"cmd": "Connected", "slot_info": normalized}])


def data_package(payload=None) -> str:
    return json.dumps([{"cmd": "DataPackage", "data": payload or DEFAULT_DATA_PACKAGE}])


def item_send(
    *,
    receiving: int = 2,
    item: int = 1,
    location: int = 10,
    player: int = 1,
    flags: int = 1,
) -> str:
    return json.dumps(
        [
            {
                "cmd": "PrintJSON",
                "type": "ItemSend",
                "receiving": receiving,
                "item": {
                    "item": item,
                    "location": location,
                    "player": player,
                    "flags": flags,
                },
            }
        ]
    )


def connection_refused(*errors: str) -> str:
    return json.dumps([{"cmd": "ConnectionRefused", "errors": list(errors)}])
