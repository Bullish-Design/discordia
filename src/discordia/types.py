# src/discordia/types.py
from __future__ import annotations

from typing import Annotated

from pydantic import Field, SecretStr, StringConstraints

# Discord snowflake IDs are positive 64-bit integers
DiscordSnowflake = Annotated[int, Field(gt=0, description="Discord snowflake ID")]

# Channel names: lowercase, hyphens, no spaces, 1-100 chars
ChannelName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9-]{1,100}$"),
    Field(description="Valid Discord channel name"),
]

# Category names: 1-100 chars, can contain spaces
CategoryName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=100),
    Field(description="Discord category name"),
]

# Message content: max 2000 chars
MessageContent = Annotated[
    str,
    StringConstraints(max_length=2000),
    Field(description="Discord message content"),
]

# Username: 2-32 chars
Username = Annotated[
    str,
    StringConstraints(min_length=2, max_length=32),
    Field(description="Discord username"),
]

# Secure credential storage
DiscordToken = SecretStr


__all__ = [
    "DiscordSnowflake",
    "ChannelName",
    "CategoryName",
    "MessageContent",
    "Username",
    "DiscordToken",
]
