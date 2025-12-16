# src/discordia/types.py
from __future__ import annotations

"""Type aliases with Pydantic validators."""

from typing import Annotated

from pydantic import AfterValidator, SecretStr


def validate_discord_id(v: int) -> int:
    """Validate Discord snowflake ID."""
    if v <= 0 or v > 2**63 - 1:
        raise ValueError(f"Invalid Discord ID: {v}")
    return v


def validate_channel_name(v: str) -> str:
    """Validate Discord channel name format.

    Discord allows lowercase alphanumeric with hyphens/underscores for regular channels,
    but threads can have spaces and mixed case.
    """
    if not v:
        raise ValueError("Channel name cannot be empty")
    if len(v) > 100:
        raise ValueError("Channel name max 100 characters")

    # Allow alphanumeric, hyphens, underscores, and spaces (for threads)
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ")
    if not all(c in allowed for c in v):
        raise ValueError("Channel name must be alphanumeric with -, _, or spaces")

    return v


def validate_username(v: str) -> str:
    """Validate Discord username."""
    if not 2 <= len(v) <= 32:
        raise ValueError("Username must be 2-32 characters")
    return v


def validate_message_content(v: str) -> str:
    """Validate message content length."""
    if len(v) > 2000:
        raise ValueError("Message content max 2000 characters")
    return v


DiscordID = Annotated[int, AfterValidator(validate_discord_id)]
ChannelName = Annotated[str, AfterValidator(validate_channel_name)]
Username = Annotated[str, AfterValidator(validate_username)]
MessageContent = Annotated[str, AfterValidator(validate_message_content)]
DiscordToken = SecretStr

__all__ = [
    "DiscordID",
    "ChannelName",
    "Username",
    "MessageContent",
    "DiscordToken",
]
