# src/discordia/settings.py
from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from discordia.types import LlmApiKey, DiscordSnowflake, DiscordToken


class Settings(BaseSettings):
    """Discordia configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Required Discord configuration
    discord_token: DiscordToken = Field(..., description="Discord bot token from developer portal")
    server_id: DiscordSnowflake = Field(..., description="Discord server (guild) ID to operate in")

    # Optional LLM configuration (None if not using LLM handlers)
    llm_api_key: LlmApiKey | None = Field(default=None, description="LLM API key for LLM integration")

    # Template and reconciliation settings
    auto_reconcile: bool = Field(default=True, description="Auto-reconcile templates to Discord on startup")
    reconcile_interval: int = Field(default=300, description="Seconds between reconciliation runs (0=disabled)")

    # Handler settings
    message_context_limit: int = Field(default=20, description="Number of messages to include in handler context")
    max_message_length: int = Field(default=2000, description="Maximum Discord message length")

    # Persistence settings
    persistence_enabled: bool = Field(default=True, description="Enable persistent state storage")
    jsonl_path: str = Field(default="discordia_state.jsonl", description="Path to JSONL state file")

    # PyGentic LLM settings
    llm_provider: str = Field(default="anthropic", description="LLM provider (anthropic, openai, google)")
    llm_model: str = Field(default="claude-sonnet-4-20250514", description="LLM model identifier")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature for generation")

    @field_validator("message_context_limit")
    @classmethod
    def _validate_message_context_limit(cls, value: int) -> int:
        if not 1 <= value <= 100:
            raise ValueError("message_context_limit must be between 1 and 100")
        return value

    @field_validator("max_message_length")
    @classmethod
    def _validate_max_message_length(cls, value: int) -> int:
        if not 1 <= value <= 2000:
            raise ValueError("max_message_length must be between 1 and 2000")
        return value

    @field_validator("reconcile_interval")
    @classmethod
    def _validate_reconcile_interval(cls, value: int) -> int:
        if value < 0:
            raise ValueError("reconcile_interval must be non-negative")
        return value
