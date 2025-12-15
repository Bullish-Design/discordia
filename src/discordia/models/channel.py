# src/discordia/models/channel.py
from __future__ import annotations

import re
from datetime import datetime
from typing import ClassVar

from pydantic import field_validator
from sqlmodel import Field
from sqlmodel._compat import SQLModelConfig

from discordia.models.base import ValidatedSQLModel


class DiscordTextChannel(ValidatedSQLModel, table=True):
    """Represents a Discord text channel.

    Text channels contain messages and may optionally belong to a parent category.
    """

    model_config = SQLModelConfig(extra="ignore")

    __tablename__ = "text_channels"

    _NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[a-z0-9-]{1,100}$")

    id: int = Field(primary_key=True, description="Discord channel ID")
    name: str = Field(max_length=100, index=True, description="Channel name")
    category_id: int | None = Field(
        default=None,
        foreign_key="categories.id",
        description="Parent category ID (None if uncategorized)",
    )
    server_id: int = Field(index=True, description="Discord server (guild) ID")
    position: int = Field(default=0, description="Display position in channel list")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When channel was created")

    @field_validator("id", "server_id")
    @classmethod
    def _validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be a positive integer")
        return value

    @field_validator("category_id")
    @classmethod
    def _validate_category_id(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("category_id must be a positive integer")
        return value

    @field_validator("name")
    @classmethod
    def _validate_channel_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Channel name cannot be blank")
        if not cls._NAME_PATTERN.match(value):
            raise ValueError("Channel name must be lowercase, use hyphens, and contain no spaces")
        return value

    def to_discord_format(self) -> dict[str, int | str | None]:
        """Convert to Discord API format."""
        return {
            "id": self.id,
            "name": self.name,
            "guild_id": self.server_id,
            "parent_id": self.category_id,
            "position": self.position,
        }
