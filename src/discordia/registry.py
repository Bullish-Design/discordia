# src/discordia/registry.py
from __future__ import annotations

"""Entity registry for convenience lookups.

The state store protocol currently provides point lookups by ID, but not list
or query operations. For the built-in in-memory store, the registry provides a
thin convenience layer for common queries.
"""

from discordia.exceptions import EntityNotFoundError
from discordia.state import Category, Channel, MemoryState, StateStore
from discordia.types import DiscordID


class EntityRegistry:
    """Convenience layer for querying known entities."""

    def __init__(self, store: StateStore):
        self._store = store

    async def get_category_by_name(self, name: str, server_id: DiscordID) -> Category:
        """Find a category by its name within a server."""

        if isinstance(self._store, MemoryState):
            async with self._store._lock:
                for category in self._store.categories.values():
                    if category.server_id == server_id and category.name == name:
                        return category
        raise EntityNotFoundError(f"Category '{name}' not found")

    async def get_channel_by_name(self, name: str, server_id: DiscordID) -> Channel:
        """Find a channel by its name within a server."""

        if isinstance(self._store, MemoryState):
            async with self._store._lock:
                for channel in self._store.channels.values():
                    if channel.server_id == server_id and channel.name == name:
                        return channel
        raise EntityNotFoundError(f"Channel '{name}' not found")

    async def get_channels_in_category(self, category_id: DiscordID) -> list[Channel]:
        """Return all channels in a category."""

        if isinstance(self._store, MemoryState):
            async with self._store._lock:
                return [channel for channel in self._store.channels.values() if channel.category_id == category_id]
        return []


__all__ = ["EntityRegistry"]
