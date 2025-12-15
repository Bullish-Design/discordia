# src/discordia/templates/generated.py
from __future__ import annotations

from pygentic import GenField, GenModel


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


__all__ = ["GeneratedChannelMeta"]
