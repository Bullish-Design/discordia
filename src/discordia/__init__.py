# src/discordia/__init__.py
from __future__ import annotations

from discordia.engine.bot import Bot
from discordia.exceptions import (
    CategoryNotFoundError,
    ChannelNotFoundError,
    ConfigurationError,
    ContextTooLargeError,
    DatabaseError,
    DiscordAPIError,
    DiscordiaError,
    HandlerError,
    JSONLError,
    LLMAPIError,
    LLMError,
    MessageSendError,
    PersistenceError,
    ReconciliationError,
    StateError,
    TemplateError,
)
from discordia.settings import Settings

__version__ = "0.2.0"

__all__ = [
    "Bot",
    "CategoryNotFoundError",
    "ChannelNotFoundError",
    "ConfigurationError",
    "ContextTooLargeError",
    "DatabaseError",
    "DiscordAPIError",
    "DiscordiaError",
    "HandlerError",
    "JSONLError",
    "LLMAPIError",
    "LLMError",
    "MessageSendError",
    "PersistenceError",
    "ReconciliationError",
    "Settings",
    "StateError",
    "TemplateError",
]
