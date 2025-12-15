# src/discordia/models/user.py
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DiscordUser(BaseModel):
    """Represents a Discord user.

    Users may be humans or bots. Discord now defaults the discriminator to "0".
    """

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Discord user ID")
    username: str = Field(..., max_length=32, description="Discord username")
    discriminator: str = Field(default="0", description="Legacy discriminator (usually '0')")
    bot: bool = Field(default=False, description="Whether the user is a bot")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the user account was created")

    @field_validator("id")
    @classmethod
    def _validate_positive_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("User ID must be a positive integer")
        return value

    @field_validator("username")
    @classmethod
    def _validate_username_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Username cannot be blank")
        return value

    @field_validator("discriminator")
    @classmethod
    def _validate_discriminator(cls, value: str) -> str:
        if not value:
            raise ValueError("Discriminator cannot be blank")
        return value

    def to_discord_format(self) -> dict[str, object]:
        """Convert to Discord API format.

        Account creation is returned as an ISO-8601 string.
        """
        return {
            "id": self.id,
            "username": self.username,
            "discriminator": self.discriminator,
            "bot": self.bot,
            "created_at": self.created_at.isoformat(),
        }
