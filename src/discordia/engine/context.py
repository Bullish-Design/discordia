# src/discordia/engine/context.py
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from discordia.state.models import Channel, Message, User
from discordia.types import DiscordSnowflake

if TYPE_CHECKING:
    from discordia.state.protocol import StateStore


@dataclass
class MessageContext:
    """Context object passed to message handlers."""

    message_id: DiscordSnowflake
    content: str
    author_id: DiscordSnowflake
    author_name: str
    channel_id: DiscordSnowflake
    channel_name: str
    channel: Channel
    author: User
    store: StateStore

    async def get_history(self, limit: int = 20) -> list[Message]:
        """Load message history from this channel."""
        return await self.store.get_messages(self.channel_id, limit=limit)

    async def reply(self, content: str) -> None:
        """Reply to this message (placeholder - actual Discord reply handled by bot)."""
        pass


__all__ = ["MessageContext"]
