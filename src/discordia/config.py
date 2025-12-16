# src/discordia/config.py
from __future__ import annotations

"""Configuration models.

This module contains immutable configuration models used to initialize a bot.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from discordia.types import DiscordID, DiscordToken


class BotConfig(BaseModel):
    """Immutable bot configuration."""

    model_config = ConfigDict(frozen=True, strict=True)

    discord_token: DiscordToken
    server_id: DiscordID
    message_context_limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def _validate_config(self) -> Self:
        # Placeholder for cross-field validations.
        return self


__all__ = [
    "BotConfig",
]
