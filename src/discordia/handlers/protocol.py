# src/discordia/handlers/protocol.py
from __future__ import annotations

from typing import Protocol, runtime_checkable

from discordia.engine.context import MessageContext


@runtime_checkable
class MessageHandler(Protocol):
    """Protocol for message handlers."""

    async def can_handle(self, ctx: MessageContext) -> bool:
        """Return True if this handler should process the message."""
        ...

    async def handle(self, ctx: MessageContext) -> str | None:
        """Process message and return optional response text."""
        ...


__all__ = ["MessageHandler"]
