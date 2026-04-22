"""Archipelago WebSocket client."""
from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

from archibot.archipelago.protocol import (
    ArchipelagoConnectionRefused,
    build_connect_packet,
    build_get_data_package_packet,
    lookup_item_name,
    lookup_location_name,
    normalize_data_package,
    normalize_slot_info,
    slot_game,
    slot_name,
)
from archibot.events import UnlockEvent

log = logging.getLogger(__name__)
EventCallback = Callable[[UnlockEvent], Awaitable[None]]


class ArchipelagoClient:
    """Stateful AP protocol parser plus optional WebSocket runner."""

    def __init__(
        self,
        host: str,
        port: int,
        slot_name_value: str,
        on_unlock: EventCallback | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.slot_name = slot_name_value
        self.on_unlock = on_unlock
        self.seed_name: str | None = None
        self.slot_info: dict[int, dict[str, Any]] = {}
        self.data_package: dict[str, Any] = {}
        self._needs_connect = False
        self._needs_data_package = False
        self._socket = None

    @property
    def players(self) -> list[str]:
        return sorted(info["name"] for info in self.slot_info.values())

    def feed(self, raw_json_frame: str) -> list[UnlockEvent]:
        try:
            payload = json.loads(raw_json_frame)
        except json.JSONDecodeError:
            log.warning("dropping malformed frame", exc_info=True)
            return []

        commands = payload if isinstance(payload, list) else [payload]
        events: list[UnlockEvent] = []
        for command in commands:
            event = self._handle_command(command)
            if event is not None:
                events.append(event)
        return events

    def _handle_command(self, command: dict[str, Any]) -> UnlockEvent | None:
        cmd = command.get("cmd")
        if cmd == "RoomInfo":
            self.seed_name = command.get("seed_name")
            self._needs_connect = True
            return None

        if cmd == "Connected":
            self.slot_info = normalize_slot_info(command.get("slot_info", {}))
            self._needs_data_package = True
            return None

        if cmd == "DataPackage":
            self.data_package.update(normalize_data_package(command.get("data", {})))
            self.data_package.update(normalize_data_package(command.get("games", {})))
            return None

        if cmd == "ConnectionRefused":
            raise ArchipelagoConnectionRefused(command.get("errors", []))

        if cmd == "PrintJSON" and command.get("type") == "ItemSend":
            return self._parse_item_send(command)

        return None

    def _parse_item_send(self, command: dict[str, Any]) -> UnlockEvent | None:
        item = command.get("item") or {}
        sender_id = int(item.get("player", 0))
        receiver_id = int(command.get("receiving", 0))
        if sender_id == 0 or sender_id == receiver_id:
            return None

        game = slot_game(self.slot_info, sender_id)
        return UnlockEvent(
            receiver_slot=slot_name(self.slot_info, receiver_id),
            sender_slot=slot_name(self.slot_info, sender_id),
            item_name=lookup_item_name(self.data_package, game, int(item.get("item", 0))),
            location_name=lookup_location_name(
                self.data_package,
                game,
                int(item.get("location", 0)),
            ),
            game=game,
            flags=int(item.get("flags", 0)),
        )

    async def run(self, password: str = "") -> None:
        url = f"ws://{self.host}:{self.port}"
        async with websockets.connect(url) as socket:
            self._socket = socket
            async for raw_frame in socket:
                events = self.feed(raw_frame)
                if self._needs_connect:
                    await socket.send(json.dumps([build_connect_packet(self.slot_name, password)]))
                    self._needs_connect = False
                if self._needs_data_package:
                    games = [info["game"] for info in self.slot_info.values() if info.get("game")]
                    if games:
                        await socket.send(json.dumps([build_get_data_package_packet(games)]))
                    self._needs_data_package = False
                if self.on_unlock is not None:
                    for event in events:
                        await self.on_unlock(event)

    async def close(self) -> None:
        if self._socket is not None:
            await self._socket.close()
