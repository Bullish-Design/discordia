# src/discordia/state.py
from __future__ import annotations

"""State models and storage protocol."""

import asyncio
from datetime import UTC, datetime
from typing import Any, Protocol, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from discordia.exceptions import StateError
from discordia.types import ChannelName, DiscordID, MessageContent, Username


def utc_now() -> datetime:
    """Current UTC time as a timezone-aware datetime."""

    return datetime.now(UTC)


def normalize_to_utc(value: datetime) -> datetime:
    """Ensure a datetime is timezone-aware and in UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class StateEntity(BaseModel):
    """Base for all stored entities."""

    model_config = ConfigDict(validate_assignment=True)

    id: DiscordID
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="before")
    @classmethod
    def _coerce_datetimes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("created_at", "updated_at"):
                value = data.get(key)
                if isinstance(value, datetime):
                    data[key] = normalize_to_utc(value)
        return data

    @model_validator(mode="after")
    def update_timestamp(self) -> Self:
        """Auto-update timestamp on changes."""
        # Avoid recursion with validate_assignment=True by bypassing pydantic's
        # __setattr__ when updating the timestamp.
        object.__setattr__(self, "updated_at", utc_now())
        return self


class Category(StateEntity):
    """Discord category."""

    name: str = Field(min_length=1, max_length=100)
    server_id: DiscordID
    position: int = Field(default=0, ge=0)


class Channel(StateEntity):
    """Discord text channel."""

    name: ChannelName
    server_id: DiscordID
    category_id: DiscordID | None = None
    position: int = Field(default=0, ge=0)
    topic: str | None = Field(default=None, max_length=1024)

    @computed_field
    @property
    def is_categorized(self) -> bool:
        return self.category_id is not None


class User(StateEntity):
    """Discord user."""

    username: Username
    discriminator: str = "0"
    bot: bool = False


class Message(StateEntity):
    """Discord message."""

    content: MessageContent
    author_id: DiscordID
    channel_id: DiscordID
    timestamp: datetime
    edited_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_message_datetimes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("timestamp", "edited_at"):
                value = data.get(key)
                if isinstance(value, datetime):
                    data[key] = normalize_to_utc(value)
        return data

    @computed_field
    @property
    def age_seconds(self) -> float:
        return (utc_now() - self.timestamp).total_seconds()

    @computed_field
    @property
    def is_edited(self) -> bool:
        return self.edited_at is not None


T = TypeVar("T", bound=StateEntity)


class StateStore(Protocol):
    """Protocol for state storage backends."""

    async def save_category(self, category: Category) -> None: ...

    async def save_channel(self, channel: Channel) -> None: ...

    async def save_user(self, user: User) -> None: ...

    async def save_message(self, message: Message) -> None: ...

    async def get_category(self, id: DiscordID) -> Category | None: ...

    async def get_channel(self, id: DiscordID) -> Channel | None: ...

    async def get_user(self, id: DiscordID) -> User | None: ...

    async def get_message(self, id: DiscordID) -> Message | None: ...

    async def get_messages(self, channel_id: DiscordID, limit: int = 20) -> list[Message]: ...


class MemoryState:
    """In-memory state storage."""

    def __init__(self):
        self.categories: dict[DiscordID, Category] = {}
        self.channels: dict[DiscordID, Channel] = {}
        self.users: dict[DiscordID, User] = {}
        self.messages: dict[DiscordID, Message] = {}
        self._lock = asyncio.Lock()

    async def save_category(self, category: Category) -> None:
        async with self._lock:
            self.categories[category.id] = category

    async def save_channel(self, channel: Channel) -> None:
        async with self._lock:
            if channel.category_id and channel.category_id not in self.categories:
                raise StateError(f"Category {channel.category_id} not found")
            self.channels[channel.id] = channel

    async def save_user(self, user: User) -> None:
        async with self._lock:
            self.users[user.id] = user

    async def save_message(self, message: Message) -> None:
        async with self._lock:
            if message.author_id not in self.users:
                raise StateError(f"User {message.author_id} not found")
            if message.channel_id not in self.channels:
                raise StateError(f"Channel {message.channel_id} not found")
            self.messages[message.id] = message

    async def get_category(self, id: DiscordID) -> Category | None:
        async with self._lock:
            return self.categories.get(id)

    async def get_channel(self, id: DiscordID) -> Channel | None:
        async with self._lock:
            return self.channels.get(id)

    async def get_user(self, id: DiscordID) -> User | None:
        async with self._lock:
            return self.users.get(id)

    async def get_message(self, id: DiscordID) -> Message | None:
        async with self._lock:
            return self.messages.get(id)

    async def get_messages(self, channel_id: DiscordID, limit: int = 20) -> list[Message]:
        async with self._lock:
            messages = [m for m in self.messages.values() if m.channel_id == channel_id]

        sorted_msgs = sorted(messages, key=lambda m: (m.timestamp, m.id))
        return sorted_msgs[-limit:] if limit > 0 else sorted_msgs


__all__ = [
    "StateEntity",
    "Category",
    "Channel",
    "User",
    "Message",
    "StateStore",
    "MemoryState",
]
