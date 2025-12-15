# src/discordia/handlers/llm.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pygentic import LLMConfig

from discordia.engine.context import MessageContext
from discordia.handlers.models import ConversationResponse
from discordia.handlers.pygentic_adapter import access_property_async, generate_async

if TYPE_CHECKING:
    from pydantic import SecretStr

logger = logging.getLogger("discordia.handlers.llm")


class LLMHandler:
    """LLM-powered message handler using PyGentic."""

    def __init__(
        self,
        api_key: SecretStr,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
    ) -> None:
        self.config = LLMConfig(provider=provider, model=model, temperature=temperature)
        ConversationResponse.set_llm_config(self.config)

    async def can_handle(self, ctx: MessageContext) -> bool:
        """Handle all messages in log channels."""
        return ctx.channel_name.count("-") == 2

    async def handle(self, ctx: MessageContext) -> str | None:
        """Generate LLM response using PyGentic."""
        history = await ctx.get_history(limit=20)
        history_text = [f"{m.author_id}: {m.content}" for m in history]

        response_model = await generate_async(
            ConversationResponse,
            channel_name=ctx.channel_name,
            channel_topic=ctx.channel.topic,
            user_name=ctx.author_name,
            user_message=ctx.content,
            history=history_text,
        )

        response = await access_property_async(response_model, "response")
        logger.info("Generated response for %s (%d chars)", ctx.channel_name, len(response))
        return response


__all__ = ["LLMHandler"]
