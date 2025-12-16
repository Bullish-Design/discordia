# src/discordia/plugins.py
from __future__ import annotations

"""Plugin framework.

Plugins provide lifecycle hooks that allow users to extend bot behavior without
interacting directly with the Discord client.
"""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from discordia.context import MessageContext


@runtime_checkable
class Plugin(Protocol):
    """Protocol for bot plugins.

    Plugins are called by the bot orchestrator during lifecycle events.
    """

    async def on_ready(self, bot: Any, guild: Any) -> None:
        """Called when the bot connects to Discord and guild sync is complete."""

    async def on_message(self, bot: Any, ctx: MessageContext) -> None:
        """Called for every message before handlers are evaluated."""


__all__ = [
    "Plugin",
]
