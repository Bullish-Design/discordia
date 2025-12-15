# examples/llm_handlers/models.py
"""PyGentic model definitions for Discord handlers."""
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


class GeneratedChannelMeta(GenModel):
    """You are a Discord server architect. Create engaging channel descriptions."""

    channel_name: str
    category_name: str
    server_purpose: str

    topic: str = GenField(
        prompt="Write a brief topic/description for #{channel_name} in the {category_name} "
        "category. Server purpose: {server_purpose}. Max 100 chars."
    )

    welcome_message: str = GenField(
        prompt="Write a friendly welcome message for #{channel_name}. "
        "Context: {server_purpose}. Max 200 chars."
    )


__all__ = ["ConversationResponse", "GeneratedChannelMeta"]
