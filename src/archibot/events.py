"""Typed domain events."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UnlockEvent:
    receiver_slot: str
    sender_slot: str
    item_name: str
    location_name: str
    game: str
    flags: int
