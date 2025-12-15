# src/discordia/handlers/logging.py
from __future__ import annotations

import logging

from discordia.engine.context import MessageContext

logger = logging.getLogger("discordia.handlers.logging")


class LoggingHandler:
    """Simple logging handler that logs messages without responding."""

    async def can_handle(self, ctx: MessageContext) -> bool:
        """Handle all messages."""
        return True

    async def handle(self, ctx: MessageContext) -> str | None:
        """Log message without responding."""
        logger.info(
            "Message in #%s from %s: %s", ctx.channel_name, ctx.author_name, ctx.content[:100]
        )
        return None


__all__ = ["LoggingHandler"]
