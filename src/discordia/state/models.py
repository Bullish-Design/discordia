# src/discordia/state/models.py
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from discordia.types import CategoryName, ChannelName, DiscordSnowflake, MessageContent, Username


class StateModel(BaseModel):
    """Base model for runtime state entities."""

    model_config = ConfigDict(extra="ignore", validate_assignment=True)


class Category(StateModel):
    """Runtime Discord category state."""

    id: DiscordSnowflake
    name: CategoryName
    server_id: DiscordSnowflake
    position: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Channel(StateModel):
    """Runtime Discord channel state."""

    id: DiscordSnowflake
    name: ChannelName
    category_id: DiscordSnowflake | None = None
    server_id: DiscordSnowflake
    position: int = 0
    topic: str | None = Field(default=None, max_length=1024)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("category_id")
    @classmethod
    def _validate_category_id(cls, value: DiscordSnowflake | None) -> DiscordSnowflake | None:
        if value is not None and value <= 0:
            raise ValueError("category_id must be a positive integer")
        return value


class User(StateModel):
    """Runtime Discord user state."""

    id: DiscordSnowflake
    username: Username
    discriminator: str = "0"
    bot: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(StateModel):
    """Runtime Discord message state."""

    id: DiscordSnowflake
    content: MessageContent
    author_id: DiscordSnowflake
    channel_id: DiscordSnowflake
    timestamp: datetime
    edited_at: datetime | None = None


__all__ = ["StateModel", "Category", "Channel", "User", "Message"]
