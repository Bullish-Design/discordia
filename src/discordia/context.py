# src/discordia/context.py
from __future__ import annotations

"""Message context passed to handlers."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from discordia.state import Channel, Message, StateStore, User
from discordia.types import DiscordID


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class MessageContext(BaseModel):
    """Rich context for a received message."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    message_id: DiscordID
    content: str
    author: User
    channel: Channel
    store: StateStore
    timestamp: datetime

    @model_validator(mode="before")
    @classmethod
    def _coerce_timestamp(cls, data: Any) -> Any:
        if isinstance(data, dict):
            ts = data.get("timestamp")
            if isinstance(ts, datetime):
                data["timestamp"] = _ensure_utc(ts)
        return data

    @computed_field
    @property
    def is_command(self) -> bool:
        """Whether the message starts with a supported command prefix."""

        return self.content.startswith(("!", "/", "."))

    @computed_field
    @property
    def command_parts(self) -> list[str]:
        """Split the command into parts."""

        return self.content.split() if self.is_command else []

    @computed_field
    @property
    def command_name(self) -> str | None:
        """Extract the command name (without the prefix)."""

        if not self.is_command or not self.command_parts:
            return None
        return self.command_parts[0][1:]

    @computed_field
    @property
    def command_args(self) -> list[str]:
        """Extract command arguments."""

        return self.command_parts[1:] if len(self.command_parts) > 1 else []

    @computed_field
    @property
    def age_ms(self) -> int:
        """Message age in milliseconds."""

        now = datetime.now(UTC)
        return int((now - self.timestamp).total_seconds() * 1000)

    @computed_field
    @property
    def mentions_bot(self) -> bool:
        """Whether the message appears to contain a user mention."""

        return "<@" in self.content

    async def get_history(self, limit: int = 20) -> list[Message]:
        """Retrieve recent message history for this channel."""

        return await self.store.get_messages(self.channel.id, limit=limit)


__all__ = ["MessageContext"]
