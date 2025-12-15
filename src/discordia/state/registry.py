# src/discordia/state/registry.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discordia.exceptions import CategoryNotFoundError, ChannelNotFoundError
from discordia.types import DiscordSnowflake

if TYPE_CHECKING:
    from discordia.state.models import Category, Channel
    from discordia.state.protocol import StateStore

logger = logging.getLogger("discordia.state.registry")


class EntityRegistry:
    """Registry for entity lookups with relationship tracking."""

    def __init__(self, store: StateStore) -> None:
        self.store = store

    async def get_category_by_name(self, name: str, server_id: DiscordSnowflake) -> Category:
        """Find category by name within a server."""
        from discordia.state.memory import MemoryState

        if isinstance(self.store, MemoryState):
            async with self.store._lock:
                for category in self.store.categories.values():
                    if category.name == name and category.server_id == server_id:
                        return category

        raise CategoryNotFoundError(f"Category '{name}' not found in server {server_id}")

    async def get_channel_by_name(self, name: str, server_id: DiscordSnowflake) -> Channel:
        """Find channel by name within a server."""
        from discordia.state.memory import MemoryState

        if isinstance(self.store, MemoryState):
            async with self.store._lock:
                for channel in self.store.channels.values():
                    if channel.name == name and channel.server_id == server_id:
                        return channel

        raise ChannelNotFoundError(f"Channel '{name}' not found in server {server_id}")

    async def get_channels_in_category(self, category_id: DiscordSnowflake) -> list[Channel]:
        """Get all channels in a category."""
        from discordia.state.memory import MemoryState

        if isinstance(self.store, MemoryState):
            async with self.store._lock:
                return [c for c in self.store.channels.values() if c.category_id == category_id]
        return []


__all__ = ["EntityRegistry"]
