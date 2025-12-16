# src/discordia/discovery.py
from __future__ import annotations

"""Discovery engine for syncing Discord state.

The discovery engine is responsible for reading categories and channels from a
Discord guild and writing validated state models into the configured store.

This module is intentionally lightweight and uses best-effort imports for
discord-py-interactions types so the core package remains testable without the
Discord library.
"""

import logging
from typing import Any

from discordia.exceptions import DiscordAPIError
from discordia.state import Category, Channel, StateStore
from discordia.types import DiscordID

logger = logging.getLogger("discordia.discovery")


try:  # pragma: no cover
    from interactions.models.discord.channel import GuildCategory, GuildText
except Exception:  # pragma: no cover

    class GuildCategory:  # noqa: D101
        pass

    class GuildText:  # noqa: D101
        pass


class DiscoveryEngine:
    """Discovers and synchronizes guild state into a :class:`~discordia.state.StateStore`."""

    def __init__(self, store: StateStore, server_id: DiscordID):
        self.store = store
        self.server_id = server_id

    async def discover_categories(self, guild: Any) -> list[Category]:
        """Discover all categories in a guild and save them to the store."""

        try:
            categories: list[Category] = []
            for channel in getattr(guild, "channels", []) or []:
                if isinstance(channel, GuildCategory):
                    category = Category(
                        id=int(channel.id),
                        name=str(channel.name),
                        server_id=self.server_id,
                        position=int(getattr(channel, "position", 0) or 0),
                    )
                    await self.store.save_category(category)
                    categories.append(category)

            logger.info("Discovered %d categories", len(categories))
            return categories
        except Exception as exc:
            logger.error("Failed to discover categories: %s", exc, exc_info=True)
            raise DiscordAPIError("Category discovery failed", cause=exc) from exc

    async def discover_channels(self, guild: Any) -> list[Channel]:
        """Discover all text channels in a guild and save them to the store."""

        try:
            channels: list[Channel] = []
            for channel in getattr(guild, "channels", []) or []:
                if not isinstance(channel, GuildText):
                    continue

                parent_id = getattr(channel, "parent_id", None)
                topic_raw = getattr(channel, "topic", None)
                topic: str | None = None
                if topic_raw:
                    topic = str(topic_raw)

                text_channel = Channel(
                    id=int(channel.id),
                    name=str(channel.name),
                    server_id=self.server_id,
                    category_id=int(parent_id) if parent_id else None,
                    position=int(getattr(channel, "position", 0) or 0),
                    topic=topic,
                )
                await self.store.save_channel(text_channel)
                channels.append(text_channel)

            logger.info("Discovered %d channels", len(channels))
            return channels
        except Exception as exc:
            logger.error("Failed to discover channels: %s", exc, exc_info=True)
            raise DiscordAPIError("Channel discovery failed", cause=exc) from exc


__all__ = [
    "DiscoveryEngine",
    "GuildCategory",
    "GuildText",
]
