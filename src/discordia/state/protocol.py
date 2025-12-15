# src/discordia/state/protocol.py
from __future__ import annotations

from typing import Protocol, runtime_checkable

from discordia.state.models import Category, Channel, Message, User
from discordia.types import DiscordSnowflake


@runtime_checkable
class StateStore(Protocol):
    """Protocol for state storage backends."""

    async def save_category(self, category: Category) -> None:
        """Save or update a category."""
        ...

    async def save_channel(self, channel: Channel) -> None:
        """Save or update a channel."""
        ...

    async def save_user(self, user: User) -> None:
        """Save or update a user."""
        ...

    async def save_message(self, message: Message) -> None:
        """Save a message."""
        ...

    async def get_category(self, category_id: DiscordSnowflake) -> Category | None:
        """Retrieve category by ID."""
        ...

    async def get_channel(self, channel_id: DiscordSnowflake) -> Channel | None:
        """Retrieve channel by ID."""
        ...

    async def get_user(self, user_id: DiscordSnowflake) -> User | None:
        """Retrieve user by ID."""
        ...

    async def get_messages(self, channel_id: DiscordSnowflake, limit: int = 20) -> list[Message]:
        """Retrieve recent messages from a channel."""
        ...


__all__ = ["StateStore"]
