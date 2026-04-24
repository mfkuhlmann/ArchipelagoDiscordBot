from unittest.mock import AsyncMock

import pytest
import websockets

from archibot.archipelago.client import ArchipelagoClient
from archibot.archipelago.protocol import ArchipelagoConnectionRefused
from tests.fixtures.ap_frames import connected, connection_refused, data_package, item_send, room_info


def test_feed_drops_self_sends_and_server_sends():
    client = ArchipelagoClient("localhost", 38281, "Meow")
    client.feed(connected())
    client.feed(data_package())
    assert client.feed(item_send(receiving=1, player=1)) == []
    assert client.feed(item_send(receiving=2, player=0)) == []


def test_feed_emits_unlock_event():
    client = ArchipelagoClient("localhost", 38281, "Meow")
    client.feed(connected())
    client.feed(data_package())
    events = client.feed(item_send())
    assert len(events) == 1
    event = events[0]
    assert event.receiver_slot == "Bork"
    assert event.sender_slot == "Meow"
    assert event.item_name == "Missile"
    assert event.location_name == "Eastern Palace - Big Chest"
    assert event.game == "A Link to the Past"


def test_feed_raises_connection_refused():
    client = ArchipelagoClient("localhost", 38281, "Meow")
    with pytest.raises(ArchipelagoConnectionRefused):
        client.feed(connection_refused("InvalidSlot"))


@pytest.mark.asyncio
async def test_run_processes_frames():
    received = []

    async def on_unlock(event):
        received.append(event)

    async def handler(websocket):
        await websocket.send(room_info())
        connect_frame = await websocket.recv()
        assert "Connect" in connect_frame
        await websocket.send(connected())
        packet = await websocket.recv()
        assert "GetDataPackage" in packet
        await websocket.send(data_package())
        await websocket.send(item_send())
        await websocket.close()

    server = await websockets.serve(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        client = ArchipelagoClient("127.0.0.1", port, "Meow", on_unlock=on_unlock)
        await client.run()
    finally:
        server.close()
        await server.wait_closed()

    assert len(received) == 1


@pytest.mark.asyncio
async def test_run_reports_room_seed():
    seeds = []

    async def on_room_info(seed_name):
        seeds.append(seed_name)

    async def handler(websocket):
        await websocket.send(room_info("Seeded Room"))
        await websocket.recv()
        await websocket.close()

    server = await websockets.serve(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        client = ArchipelagoClient(
            "127.0.0.1",
            port,
            "Meow",
            on_room_info=on_room_info,
        )
        await client.run()
    finally:
        server.close()
        await server.wait_closed()

    assert seeds == ["Seeded Room"]
