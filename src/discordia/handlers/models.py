# src/discordia/handlers/models.py
from __future__ import annotations

from pygentic import GenField, GenModel


class ConversationResponse(GenModel):
    """You are a helpful Discord bot assistant responding to user messages."""

    channel_name: str
    channel_topic: str | None
    user_name: str
    user_message: str
    history: list[str]

    response: str = GenField(
        prompt="Channel: #{channel_name}\n"
        "Topic: {channel_topic}\n"
        "User: {user_name}\n"
        "Message: {user_message}\n\n"
        "Recent history:\n{history}\n\n"
        "Respond naturally and helpfully. Max 1500 chars."
    )


__all__ = ["ConversationResponse"]
