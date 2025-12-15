# src/discordia/models/category.py
from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from discordia.models.base import DiscordiaModel


class DiscordCategory(DiscordiaModel):
    """Represents a Discord channel category.

    Categories group related channels together in Discord servers.
    """

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Discord category ID")
    name: str = Field(..., max_length=100, description="Category name")
    server_id: int = Field(..., description="Discord server (guild) ID")
    position: int = Field(default=0, description="Display position in channel list")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When category was created")

    @field_validator("id", "server_id")
    @classmethod
    def _validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be a positive integer")
        return value

    @field_validator("name")
    @classmethod
    def _validate_name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Category name cannot be blank")
        return value

    def to_discord_format(self) -> dict[str, int | str]:
        """Convert to Discord API format."""
        return {
            "id": self.id,
            "name": self.name,
            "guild_id": self.server_id,
            "position": self.position,
        }
