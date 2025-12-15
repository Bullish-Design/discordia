# src/discordia/handlers/weekday_handler.py
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from pygentic import LLMConfig

from discordia.engine.context import MessageContext
from discordia.handlers.models import ConversationResponse
from discordia.handlers.pygentic_adapter import access_property_async, generate_async

if TYPE_CHECKING:
    from pydantic import SecretStr

logger = logging.getLogger("discordia.handlers.weekday")

# Pattern matches WW-DD format (01-99 week, 01-07 day)
WEEKDAY_PATTERN = re.compile(r"^\d{2}-\d{2}-0[1-7]$")


class WeekDayHandler:
    """LLM handler that responds to messages in WW-DD format channels."""

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
        """Handle messages in WW-DD format channels."""

        allowed = bool(WEEKDAY_PATTERN.match(ctx.channel_name))
        logger.info(f"Can handle in channel '{ctx.channel_name}': {allowed}")
        return allowed

    async def handle(self, ctx: MessageContext) -> str | None:
        """Generate LLM response using PyGentic."""
        logger.info("Handling message in channel '%s'", ctx.channel_name)
        history = await ctx.get_history(limit=20)
        logger.info("Fetched %d messages for context", len(history))
        history_text = [f"{m.author_id}: {m.content}" for m in history]
        logger.info(f"Prepared history text with {len(history_text)} entries")


        response_model = await generate_async(
            ConversationResponse,
            channel_name=ctx.channel_name,
            channel_topic=ctx.channel.topic,
            user_name=ctx.author_name,
            user_message=ctx.content,
            history=history_text,
        )
        logger.info(f"Generated response model: {response_model}")
        response = await access_property_async(response_model, "response")
        logger.info("Generated response for %s (%d chars)", ctx.channel_name, len(response))
        return response


__all__ = ["WeekDayHandler"]
