# src/discordia/__init__.py
from __future__ import annotations

from discordia.bot import Bot, setup_logging
from discordia.exceptions import (
    CategoryNotFoundError,
    ChannelNotFoundError,
    ConfigurationError,
    ContextTooLargeError,
    DatabaseError,
    DiscordAPIError,
    DiscordiaError,
    JSONLError,
    LLMAPIError,
    LLMError,
    MessageSendError,
    PersistenceError,
    ValidationError,
)
from discordia.settings import Settings

__version__ = "0.1.0"

__all__ = [
    "Bot",
    "CategoryNotFoundError",
    "ChannelNotFoundError",
    "ConfigurationError",
    "ContextTooLargeError",
    "DatabaseError",
    "DiscordAPIError",
    "DiscordiaError",
    "JSONLError",
    "LLMAPIError",
    "LLMError",
    "MessageSendError",
    "PersistenceError",
    "ValidationError",
    "Settings",
    "setup_logging",
]
