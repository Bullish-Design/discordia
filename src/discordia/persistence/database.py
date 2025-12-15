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

        await self._ensure_initialized()
        async with self._lock:
            self._state.categories[category.id] = category

    async def save_channel(self, channel: DiscordTextChannel) -> None:
        """Save or update a text channel.

        Raises:
            DatabaseError: If the referenced category does not exist.
        """

        await self._ensure_initialized()
        async with self._lock:
            if channel.category_id is not None and channel.category_id not in self._state.categories:
                raise DatabaseError(f"Failed to save channel {channel.id}: missing category {channel.category_id}")
            self._state.channels[channel.id] = channel

    async def save_user(self, user: DiscordUser) -> None:
        """Save or update a user."""

        await self._ensure_initialized()
        async with self._lock:
            self._state.users[user.id] = user

    async def save_message(self, message: DiscordMessage) -> None:
        """Save a message.

        Raises:
            DatabaseError: If author or channel references do not exist.
        """

        await self._ensure_initialized()
        async with self._lock:
            if message.author_id not in self._state.users:
                raise DatabaseError(f"Failed to save message {message.id}: missing user {message.author_id}")
            if message.channel_id not in self._state.channels:
                raise DatabaseError(f"Failed to save message {message.id}: missing channel {message.channel_id}")
            self._state.messages[message.id] = message

    async def get_category(self, category_id: int) -> DiscordCategory | None:
        """Retrieve a category by ID."""

        await self._ensure_initialized()
        async with self._lock:
            return self._state.categories.get(category_id)

    async def get_category_by_name(self, name: str, server_id: int) -> DiscordCategory | None:
        """Retrieve a category by name within a server."""

        await self._ensure_initialized()
        async with self._lock:
            for category in self._state.categories.values():
                if category.name == name and category.server_id == server_id:
                    return category
            return None

    async def get_channel(self, channel_id: int) -> DiscordTextChannel | None:
        """Retrieve a channel by ID."""

        await self._ensure_initialized()
        async with self._lock:
            return self._state.channels.get(channel_id)

    async def get_channel_by_name(self, name: str, server_id: int) -> DiscordTextChannel | None:
        """Retrieve a channel by name within a server."""

        await self._ensure_initialized()
        async with self._lock:
            for channel in self._state.channels.values():
                if channel.name == name and channel.server_id == server_id:
                    return channel
            return None

    async def get_messages(self, channel_id: int, limit: int = 20) -> list[DiscordMessage]:
        """Retrieve recent messages from a channel.

        Returns messages ordered chronologically (oldest to newest) and limited to
        the most recent `limit` messages.
        """

        await self._ensure_initialized()
        async with self._lock:
            messages = [m for m in self._state.messages.values() if m.channel_id == channel_id]
        return self._select_recent(messages, limit)

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
