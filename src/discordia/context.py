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

    @computed_field
    @property
    def is_in_thread(self) -> bool:
        """Whether the message was sent in a thread."""

        return self.channel.is_thread

    @computed_field
    @property
    def is_reply(self) -> bool:
        """Whether this message is a reply to another message."""

        return "<reply:" in self.content or self._check_reply_in_store()

    def _check_reply_in_store(self) -> bool:
        """Check if message in store has replied_to_id set."""
        # This is a fallback - we'll populate replied_to_id in bot.py
        return False

    async def get_parent_channel(self) -> Channel | None:
        """Get the parent channel if this message is in a thread."""

        if not self.is_in_thread or not self.channel.parent_channel_id:
            return None
        return await self.store.get_channel(self.channel.parent_channel_id)

    async def get_replied_message(self) -> Message | None:
        """Get the message this is replying to, if any."""

        message = await self.store.get_message(self.message_id)
        if message and message.replied_to_id:
            return await self.store.get_message(message.replied_to_id)
        return None

    async def get_history(self, limit: int = 20) -> list[Message]:
        """Retrieve recent message history for this channel."""

        return await self.store.get_messages(self.channel.id, limit=limit)


__all__ = ["MessageContext"]
