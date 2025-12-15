# examples/llm_handlers/llm_handler.py
"""LLM-powered message handler using PyGentic."""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from pygentic import LLMConfig

from discordia import MessageContext

from examples.llm_handlers.models import ConversationResponse
from examples.llm_handlers.pygentic_adapter import access_property_async, generate_async

if TYPE_CHECKING:
    from pydantic import SecretStr

logger = logging.getLogger("examples.llm_handlers.llm")


class LLMHandler:
    """LLM-powered message handler using PyGentic."""

    def __init__(
        self,
        api_key: SecretStr,
        provider: str = "openai",
        model: str = "gpt-5-nano",
        temperature: float = 1, # gpt-5-nano doesnt accept anything but 1? 0.7,
        channel_pattern: str | None = None,
    ) -> None:
        self.config = LLMConfig(provider=provider, model=model, temperature=temperature, api_key=api_key.get_secret_value(),)
        self.channel_pattern = re.compile(channel_pattern) if channel_pattern else None
        ConversationResponse.set_llm_config(self.config)

    async def can_handle(self, ctx: MessageContext) -> bool:
        """Handle messages matching channel pattern, or all if no pattern set."""
        if self.channel_pattern is None:
            return True
        return bool(self.channel_pattern.match(ctx.channel_name))

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
        if response:
            logger.info("Generated response for %s (%d chars)", ctx.channel_name, len(response))
        else:
            logger.warning("No response generated for %s", ctx.channel_name)
        return response


__all__ = ["LLMHandler"]
