# examples/llm_handlers/weekday_handler.py
"""LLM handler specifically for weekday-pattern channels."""
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

logger = logging.getLogger("examples.llm_handlers.weekday")

# Pattern matches YYYY-WW-DD format (4-digit year, 01-53 week, 01-07 day)
WEEKDAY_PATTERN = re.compile(r"^\d{4}-\d{2}-0[1-7]$")


class WeekDayHandler:
    """LLM handler that responds to messages in YYYY-WW-DD format channels."""

    def __init__(
        self,
        api_key: SecretStr,
        provider: str = "openai",
        model: str = "gpt-5-nano",
        temperature: float = 0.7,
    ) -> None:
        self.config = LLMConfig(provider=provider, model=model, temperature=temperature, 
            api_key=api_key.get_secret_value(),)
        ConversationResponse.set_llm_config(self.config)

    async def can_handle(self, ctx: MessageContext) -> bool:
        """Handle messages in YYYY-WW-DD format channels."""
        allowed = bool(WEEKDAY_PATTERN.match(ctx.channel_name))
        logger.debug("Can handle channel '%s': %s", ctx.channel_name, allowed)
        return allowed

    async def handle(self, ctx: MessageContext) -> str | None:
        """Generate LLM response using PyGentic."""
        logger.info("Handling message in channel '%s'", ctx.channel_name)
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


__all__ = ["WeekDayHandler"]
