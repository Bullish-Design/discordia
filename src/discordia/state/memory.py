# src/discordia/state/memory.py
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from discordia.exceptions import StateError
from discordia.state.models import Category, Channel, Message, User
from discordia.types import DiscordSnowflake

logger = logging.getLogger("discordia.state.memory")


@dataclass
class MemoryState:
    """In-memory state storage implementation."""

    categories: dict[DiscordSnowflake, Category] = field(default_factory=dict)
    channels: dict[DiscordSnowflake, Channel] = field(default_factory=dict)
    users: dict[DiscordSnowflake, User] = field(default_factory=dict)
    messages: dict[DiscordSnowflake, Message] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def save_category(self, category: Category) -> None:
        """Save or update a category."""
        async with self._lock:
            self.categories[category.id] = category
        logger.debug("Saved category %s", category.id)

    async def save_channel(self, channel: Channel) -> None:
        """Save or update a channel."""
        async with self._lock:
            if channel.category_id is not None and channel.category_id not in self.categories:
                raise StateError(f"Category {channel.category_id} not found for channel {channel.id}")
            self.channels[channel.id] = channel
        logger.debug("Saved channel %s", channel.id)

    async def save_user(self, user: User) -> None:
        """Save or update a user."""
        async with self._lock:
            self.users[user.id] = user
        logger.debug("Saved user %s", user.id)

    async def save_message(self, message: Message) -> None:
        """Save a message."""
        async with self._lock:
            if message.author_id not in self.users:
                raise StateError(f"User {message.author_id} not found for message {message.id}")
            if message.channel_id not in self.channels:
                raise StateError(f"Channel {message.channel_id} not found for message {message.id}")
            self.messages[message.id] = message
        logger.debug("Saved message %s", message.id)

    async def get_category(self, category_id: DiscordSnowflake) -> Category | None:
        """Retrieve category by ID."""
        async with self._lock:
            return self.categories.get(category_id)

    async def get_channel(self, channel_id: DiscordSnowflake) -> Channel | None:
        """Retrieve channel by ID."""
        async with self._lock:
            return self.channels.get(channel_id)

    async def get_user(self, user_id: DiscordSnowflake) -> User | None:
        """Retrieve user by ID."""
        async with self._lock:
            return self.users.get(user_id)

    async def get_messages(self, channel_id: DiscordSnowflake, limit: int = 20) -> list[Message]:
        """Retrieve recent messages from a channel."""
        async with self._lock:
            messages = [m for m in self.messages.values() if m.channel_id == channel_id]
        ordered = sorted(messages, key=lambda m: (m.timestamp, m.id))
        return ordered[-limit:] if limit > 0 else ordered


__all__ = ["MemoryState"]
