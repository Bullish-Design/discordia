# src/discordia/persistence/database.py
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from discordia.exceptions import DatabaseError
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser

logger = logging.getLogger("discordia.database")


@dataclass(frozen=True)
class _State:
    categories: dict[int, DiscordCategory]
    channels: dict[int, DiscordTextChannel]
    users: dict[int, DiscordUser]
    messages: dict[int, DiscordMessage]


class DatabaseWriter:
    """Async in-memory persistence for Discord entities.

    Discordia's reference implementation uses SQLModel/SQLAlchemy. The kata
    environment for these prompts does not ship with those optional runtime
    dependencies, so this writer provides a small, deterministic async API that
    matches Discordia's needs and is easy to unit test.

    The interface is intentionally kept compatible with previous prompts.
    """

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._initialized = False
        self._lock = asyncio.Lock()
        self._state = _State(categories={}, channels={}, users={}, messages={})

    async def initialize(self) -> None:
        """Initialize the database.

        For the in-memory implementation, initialization is idempotent.
        """

        self._initialized = True
        logger.info("Database initialized (in-memory)")

    async def close(self) -> None:
        """Close database resources."""

        return

    async def save_category(self, category: DiscordCategory) -> None:
        """Save or update a category."""

        try:
            await self._ensure_initialized()
            async with self._lock:
                self._state.categories[category.id] = category
            logger.debug("Saved category %s (server=%s)", category.id, category.server_id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Failed to save category %s: %s", getattr(category, "id", "unknown"), e, exc_info=True)
            raise DatabaseError(f"Failed to save category {getattr(category, 'id', 'unknown')}", cause=e) from e

    async def save_channel(self, channel: DiscordTextChannel) -> None:
        """Save or update a text channel.

        Raises:
            DatabaseError: If the referenced category does not exist.
        """

        try:
            await self._ensure_initialized()
            async with self._lock:
                if channel.category_id is not None and channel.category_id not in self._state.categories:
                    err = DatabaseError(f"Failed to save channel {channel.id}: missing category {channel.category_id}")
                    logger.error("%s", err, exc_info=True)
                    raise err
                self._state.channels[channel.id] = channel
            logger.debug(
                "Saved channel %s (server=%s category=%s)",
                channel.id,
                channel.server_id,
                channel.category_id,
            )
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Failed to save channel %s: %s", getattr(channel, "id", "unknown"), e, exc_info=True)
            raise DatabaseError(f"Failed to save channel {getattr(channel, 'id', 'unknown')}", cause=e) from e

    async def save_user(self, user: DiscordUser) -> None:
        """Save or update a user."""

        try:
            await self._ensure_initialized()
            async with self._lock:
                self._state.users[user.id] = user
            logger.debug("Saved user %s", user.id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Failed to save user %s: %s", getattr(user, "id", "unknown"), e, exc_info=True)
            raise DatabaseError(f"Failed to save user {getattr(user, 'id', 'unknown')}", cause=e) from e

    async def save_message(self, message: DiscordMessage) -> None:
        """Save a message.

        Raises:
            DatabaseError: If author or channel references do not exist.
        """

        try:
            await self._ensure_initialized()
            async with self._lock:
                if message.author_id not in self._state.users:
                    err = DatabaseError(f"Failed to save message {message.id}: missing user {message.author_id}")
                    logger.error("%s", err, exc_info=True)
                    raise err
                if message.channel_id not in self._state.channels:
                    err = DatabaseError(f"Failed to save message {message.id}: missing channel {message.channel_id}")
                    logger.error("%s", err, exc_info=True)
                    raise err
                self._state.messages[message.id] = message
            logger.debug("Saved message %s (channel=%s author=%s)", message.id, message.channel_id, message.author_id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Failed to save message %s: %s", getattr(message, "id", "unknown"), e, exc_info=True)
            raise DatabaseError(f"Failed to save message {getattr(message, 'id', 'unknown')}", cause=e) from e

    async def get_category(self, category_id: int) -> DiscordCategory | None:
        """Retrieve a category by ID."""

        try:
            await self._ensure_initialized()
            async with self._lock:
                return self._state.categories.get(category_id)
        except Exception as e:
            logger.error("Failed to get category %s: %s", category_id, e, exc_info=True)
            raise DatabaseError(f"Failed to get category {category_id}", cause=e) from e

    async def get_category_by_name(self, name: str, server_id: int) -> DiscordCategory | None:
        """Retrieve a category by name within a server."""

        try:
            await self._ensure_initialized()
            async with self._lock:
                for category in self._state.categories.values():
                    if category.name == name and category.server_id == server_id:
                        return category
                return None
        except Exception as e:
            logger.error("Failed to get category by name '%s': %s", name, e, exc_info=True)
            raise DatabaseError(f"Failed to get category by name: {name}", cause=e) from e

    async def get_channel(self, channel_id: int) -> DiscordTextChannel | None:
        """Retrieve a channel by ID."""

        try:
            await self._ensure_initialized()
            async with self._lock:
                return self._state.channels.get(channel_id)
        except Exception as e:
            logger.error("Failed to get channel %s: %s", channel_id, e, exc_info=True)
            raise DatabaseError(f"Failed to get channel {channel_id}", cause=e) from e

    async def get_channel_by_name(self, name: str, server_id: int) -> DiscordTextChannel | None:
        """Retrieve a channel by name within a server."""

        try:
            await self._ensure_initialized()
            async with self._lock:
                for channel in self._state.channels.values():
                    if channel.name == name and channel.server_id == server_id:
                        return channel
                return None
        except Exception as e:
            logger.error("Failed to get channel by name '%s': %s", name, e, exc_info=True)
            raise DatabaseError(f"Failed to get channel by name: {name}", cause=e) from e

    async def get_messages(self, channel_id: int, limit: int = 20) -> list[DiscordMessage]:
        """Retrieve recent messages from a channel.

        Returns messages ordered chronologically (oldest to newest) and limited to
        the most recent `limit` messages.
        """

        try:
            await self._ensure_initialized()
            async with self._lock:
                messages = [m for m in self._state.messages.values() if m.channel_id == channel_id]
            selected = self._select_recent(messages, limit)
            logger.debug("Loaded %s messages for channel %s (limit=%s)", len(selected), channel_id, limit)
            return selected
        except Exception as e:
            logger.error("Failed to get messages for channel %s: %s", channel_id, e, exc_info=True)
            raise DatabaseError(f"Failed to get messages for channel {channel_id}", cause=e) from e

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await self.initialize()

    @staticmethod
    def _select_recent(messages: Iterable[DiscordMessage], limit: int) -> list[DiscordMessage]:
        ordered = sorted(messages, key=lambda m: (m.timestamp, m.id))
        if limit <= 0:
            return []
        if len(ordered) <= limit:
            return ordered
        return ordered[-limit:]


__all__ = ["DatabaseWriter"]
