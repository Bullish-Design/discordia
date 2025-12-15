# src/discordia/handlers/router.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discordia.engine.context import MessageContext
    from discordia.handlers.protocol import MessageHandler

logger = logging.getLogger("discordia.handlers.router")


class HandlerRouter:
    """Routes messages to registered handlers."""

    def __init__(self, handlers: list[MessageHandler]) -> None:
        self.handlers = handlers

    async def route(self, ctx: MessageContext) -> str | None:
        """Find first handler that can process message."""
        for handler in self.handlers:
            try:
                if await handler.can_handle(ctx):
                    response = await handler.handle(ctx)
                    logger.debug("Handler %s processed message", handler.__class__.__name__)
                    return response
            except Exception as e:
                logger.error("Handler %s failed: %s", handler.__class__.__name__, e, exc_info=True)
        return None


__all__ = ["HandlerRouter"]
