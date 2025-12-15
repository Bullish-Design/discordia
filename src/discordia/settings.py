# src/discordia/settings.py
from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Discordia configuration settings.

    Loads values from environment variables (and optionally a .env file).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Required Discord configuration
    discord_token: str = Field(..., description="Discord bot token from developer portal")
    server_id: int = Field(..., description="Discord server (guild) ID to operate in")

    # Required LLM configuration
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude access")

    # Optional with defaults
    log_category_name: str = Field(default="Log", description="Category name for daily log channels")
    auto_create_daily_logs: bool = Field(default=True, description="Auto-create YYYY-MM-DD log channels")
    database_url: str = Field(
        default="sqlite+aiosqlite:///discordia.db",
        description="SQLAlchemy database URL for SQLite persistence",
    )
    jsonl_path: str = Field(default="discordia_backup.jsonl", description="Path to JSONL backup file")
    llm_model: str = Field(default="claude-sonnet-4-20250514", description="Anthropic model name")
    message_context_limit: int = Field(default=20, description="Number of messages to include in LLM context")
    max_message_length: int = Field(default=2000, description="Maximum Discord message length")

    @field_validator("server_id")
    @classmethod
    def _validate_server_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("server_id must be a positive integer")
        return value

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
