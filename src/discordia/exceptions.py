# src/discordia/exceptions.py
from __future__ import annotations

from pydantic import ValidationError


def _default_message_for(exc_type: type[BaseException]) -> str:
    """Derive a default message from an exception type."""

    name = exc_type.__name__
    spaced = "".join((" " + c if c.isupper() and i > 0 else c) for i, c in enumerate(name)).strip()
    return spaced


class DiscordiaError(Exception):
    """Base exception for all Discordia errors.

    All Discordia exceptions support an optional human-friendly message and an optional underlying
    cause. The cause is included in the string representation to aid debugging.
    """

    message: str
    cause: Exception | None

    def __init__(self, message: str | None = None, cause: Exception | None = None) -> None:
        self.message = message if message is not None else _default_message_for(type(self))
        self.cause = cause
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.cause is not None:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class ConfigurationError(DiscordiaError):
    """Raised when configuration or settings are invalid or missing."""


class DiscordAPIError(DiscordiaError):
    """Raised when a Discord API operation fails."""


class ChannelNotFoundError(DiscordAPIError):
    """Raised when a requested channel cannot be found."""


class CategoryNotFoundError(DiscordAPIError):
    """Raised when a requested category cannot be found."""


class MessageSendError(DiscordAPIError):
    """Raised when sending a message to Discord fails."""


class PersistenceError(DiscordiaError):
    """Raised when persistence operations (database/JSONL) fail."""


class DatabaseError(PersistenceError):
    """Raised when database operations fail."""


class JSONLError(PersistenceError):
    """Raised when JSONL read/write operations fail."""


class LLMError(DiscordiaError):
    """Raised when an LLM provider operation fails."""


class LLMAPIError(LLMError):
    """Raised when an LLM API call fails."""


class ContextTooLargeError(LLMError):
    """Raised when LLM context exceeds model limits."""


__all__ = [
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
]
