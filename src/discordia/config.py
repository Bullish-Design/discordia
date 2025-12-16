# src/discordia/config.py
from __future__ import annotations

"""Configuration models.

This module contains immutable configuration models used to initialize a bot.
"""

from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from discordia.types import DiscordID, DiscordToken


class BotConfig(BaseSettings):
    """Immutable bot configuration.

    Loads from environment variables with DISCORDIA_ prefix.
    Supports .env file via python-dotenv.

    Environment variables:
        DISCORDIA_DISCORD_TOKEN: Discord bot token
        DISCORDIA_SERVER_ID: Discord server/guild ID
        DISCORDIA_MESSAGE_CONTEXT_LIMIT: Message history limit (default: 20)
    """

    model_config = SettingsConfigDict(
        frozen=True,
        strict=True,
        env_prefix="DISCORDIA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    discord_token: DiscordToken
    server_id: DiscordID
    message_context_limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def _validate_config(self) -> Self:
        # Placeholder for cross-field validations.
        return self

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> Self:
        """Load configuration from environment variables and optional .env file.

        Args:
            env_file: Path to .env file. Defaults to ".env" in current directory.
                     Pass None to disable .env file loading.

        Returns:
            Configured BotConfig instance.
        """
        if env_file is None:
            return cls(_env_file=None)
        return cls(_env_file=str(env_file))


__all__ = [
    "BotConfig",
]
