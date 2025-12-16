# src/discordia/exceptions.py
from __future__ import annotations

"""Custom exceptions for Discordia."""


class DiscordiaError(Exception):
    """Base exception for all Discordia errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class ConfigurationError(DiscordiaError):
    """Invalid configuration."""


class StateError(DiscordiaError):
    """State management error."""


class DiscordAPIError(DiscordiaError):
    """Discord API operation failed."""


class EntityNotFoundError(StateError):
    """Entity not found in state."""


class ValidationError(DiscordiaError):
    """Validation failed."""


__all__ = [
    "DiscordiaError",
    "ConfigurationError",
    "StateError",
    "DiscordAPIError",
    "EntityNotFoundError",
    "ValidationError",
]
