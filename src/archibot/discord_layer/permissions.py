"""Permission helpers for slash commands."""
from __future__ import annotations


def is_moderator(user, role_name: str) -> bool:
    permissions = getattr(user, "guild_permissions", None)
    if permissions is not None and getattr(permissions, "manage_channels", False):
        return True
    for role in getattr(user, "roles", []):
        if getattr(role, "name", None) == role_name:
            return True
    return False
