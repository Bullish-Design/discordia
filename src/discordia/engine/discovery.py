# src/discordia/engine/discovery.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discordia.exceptions import DiscordAPIError
from discordia.state.models import Category, Channel
from discordia.types import DiscordSnowflake

if TYPE_CHECKING:
    from discordia.state.protocol import StateStore

logger = logging.getLogger("discordia.engine.discovery")


try:
    from interactions.models.discord.channel import GuildCategory, GuildText
except Exception:

    class GuildCategory:
        pass

    class GuildText:
        pass


class DiscoveryEngine:
    """Discovers and syncs Discord state to storage."""

    def __init__(self, store: StateStore, server_id: DiscordSnowflake) -> None:
        self.store = store
        self.server_id = server_id

    async def discover_categories(self, guild: Any) -> list[Category]:
        """Discover all categories in a guild."""
        try:
            categories: list[Category] = []
            for channel in getattr(guild, "channels", []):
                if isinstance(channel, GuildCategory):
                    category = Category(
                        id=int(channel.id),
                        name=str(channel.name),
                        server_id=self.server_id,
                        position=int(getattr(channel, "position", 0) or 0),
                    )
                    await self.store.save_category(category)
                    categories.append(category)
            logger.info("Discovered %s categories", len(categories))
            return categories
        except Exception as e:
            logger.error("Failed to discover categories: %s", e, exc_info=True)
            raise DiscordAPIError("Failed to discover categories", cause=e) from e

    async def discover_channels(self, guild: Any) -> list[Channel]:
        """Discover all text channels in a guild."""
        try:
            channels: list[Channel] = []
            for channel in getattr(guild, "channels", []):
                if isinstance(channel, GuildText):
                    parent_id = getattr(channel, "parent_id", None)
                    text_channel = Channel(
                        id=int(channel.id),
                        name=str(channel.name),
                        category_id=int(parent_id) if parent_id else None,
                        server_id=self.server_id,
                        position=int(getattr(channel, "position", 0) or 0),
                        topic=str(getattr(channel, "topic", "") or ""),
                    )
                    await self.store.save_channel(text_channel)
                    channels.append(text_channel)
            logger.info("Discovered %s channels", len(channels))
            return channels
        except Exception as e:
            logger.error("Failed to discover channels: %s", e, exc_info=True)
            raise DiscordAPIError("Failed to discover channels", cause=e) from e


__all__ = ["DiscoveryEngine"]
