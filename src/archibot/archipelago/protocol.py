"""Protocol helpers for Archipelago WebSocket messages."""
from __future__ import annotations

from typing import Any

TRACKER_TAG = "Tracker"
PROGRESSION = 0b001
USEFUL = 0b010
TRAP = 0b100


class ArchipelagoConnectionRefused(RuntimeError):
    """Raised when the AP server rejects the connection."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(", ".join(errors) if errors else "Connection refused")


def build_connect_packet(slot_name: str, password: str = "") -> dict[str, Any]:
    return {
        "cmd": "Connect",
        "game": "",
        "name": slot_name,
        "password": password,
        "tags": [TRACKER_TAG],
        "version": {"major": 0, "minor": 6, "build": 0, "class": "Version"},
        "items_handling": 0,
        "uuid": "archibot",
    }


def build_get_data_package_packet(games: list[str]) -> dict[str, Any]:
    return {"cmd": "GetDataPackage", "games": sorted(set(games))}


def normalize_slot_info(slot_info: dict[str, Any] | dict[int, Any]) -> dict[int, dict[str, Any]]:
    normalized: dict[int, dict[str, Any]] = {}
    for key, value in slot_info.items():
        normalized[int(key)] = dict(value)
    return normalized


def slot_name(slot_info: dict[int, dict[str, Any]], slot_id: int) -> str:
    if slot_id == 0:
        return "Server"
    return slot_info.get(slot_id, {}).get("name", f"slot[{slot_id}]")


def slot_game(slot_info: dict[int, dict[str, Any]], slot_id: int) -> str:
    return slot_info.get(slot_id, {}).get("game", "Unknown Game")


def lookup_item_name(
    data_package: dict[str, Any],
    game: str,
    item_id: int,
) -> str:
    return (
        data_package.get(game, {}).get("item_id_to_name", {}).get(str(item_id))
        or f"item[{item_id}]"
    )


def lookup_location_name(
    data_package: dict[str, Any],
    game: str,
    location_id: int,
) -> str:
    return (
        data_package.get(game, {}).get("location_id_to_name", {}).get(str(location_id))
        or f"location[{location_id}]"
    )


def normalize_data_package(payload: dict[str, Any]) -> dict[str, Any]:
    games = payload.get("games", payload)
    normalized: dict[str, Any] = {}
    for game, game_payload in games.items():
        normalized[game] = {
            "item_id_to_name": {
                str(value): key for key, value in game_payload.get("item_name_to_id", {}).items()
            },
            "location_id_to_name": {
                str(value): key
                for key, value in game_payload.get("location_name_to_id", {}).items()
            },
        }
    return normalized


def emoji_for_flags(flags: int) -> str:
    if flags & TRAP:
        return "🔴"
    if flags & PROGRESSION:
        return "🟣"
    if flags & USEFUL:
        return "🔵"
    return "⚪"
