# src/discordia/handlers.py
from __future__ import annotations

"""Handler framework.

Handlers are the primary extension mechanism for message processing. Each
handler decides whether it can handle a message (via :meth:`can_handle`) and
optionally returns a string response.
"""

import logging
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from discordia.context import MessageContext

logger = logging.getLogger("discordia.handlers")

TConfig = TypeVar("TConfig", bound=BaseModel)


class Handler(BaseModel, Generic[TConfig]):
    """Base handler with validated config."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: TConfig

    async def can_handle(self, ctx: MessageContext) -> bool:
        """Return True if this handler should process the message."""

        raise NotImplementedError

    async def handle(self, ctx: MessageContext) -> str | None:
        """Process message and return optional response."""

        raise NotImplementedError


class LoggingConfig(BaseModel):
    """Configuration for :class:`LoggingHandler`."""

    enabled: bool = True
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def _validate_level(cls, value: str) -> str:
        level = value.upper().strip()
        if not hasattr(logging, level):
            raise ValueError(f"Unknown log level: {value}")
        return level


class LoggingHandler(Handler[LoggingConfig]):
    """Handler that logs all messages."""

    def __init__(self, config: LoggingConfig | None = None):
        super().__init__(config=config or LoggingConfig())

    async def can_handle(self, ctx: MessageContext) -> bool:
        return self.config.enabled

    async def handle(self, ctx: MessageContext) -> str | None:
        level = getattr(logging, self.config.log_level, logging.INFO)
        print(f"[LoggingHandler] Logging message at level {level}")
        logger.log(
            level,
            "Message in #%s from %s: %s",
            ctx.channel.name,
            ctx.author.username,
            ctx.content[:100],
        )
        return None


class EchoConfig(BaseModel):
    """Configuration for :class:`EchoHandler`."""

    prefix: str = Field(default="echo:", min_length=1)


class EchoHandler(Handler[EchoConfig]):
    """Handler that echoes messages that match a prefix."""

    def __init__(self, config: EchoConfig | None = None):
        super().__init__(config=config or EchoConfig())

    async def can_handle(self, ctx: MessageContext) -> bool:
        return ctx.content.startswith(self.config.prefix)

    async def handle(self, ctx: MessageContext) -> str | None:
        return ctx.content[len(self.config.prefix) :].strip()


__all__ = [
    "Handler",
    "LoggingHandler",
    "LoggingConfig",
    "EchoHandler",
    "EchoConfig",
]
