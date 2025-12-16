# tests/test_integration.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import SecretStr

from discordia import Bot, BotConfig, EchoConfig, EchoHandler, LoggingHandler


@dataclass
class _DummyClient:
    user: Any
    listeners: list[Any] = field(default_factory=list)

    def add_listener(self, listener: Any) -> None:
        self.listeners.append(listener)

    def start(self) -> None:  # pragma: no cover
        raise RuntimeError("Dummy client cannot start")

    async def stop(self) -> None:  # pragma: no cover
        return None


def test_full_bot_assembly_and_public_imports() -> None:
    config = BotConfig(
        discord_token=SecretStr("test_token"),
        server_id=123456789,
        message_context_limit=30,
    )

    handlers = [
        LoggingHandler(),
        EchoHandler(config=EchoConfig(prefix="repeat:")),
    ]

    bot = Bot(config=config, handlers=handlers, client=_DummyClient(user=object()))

    assert bot.config.message_context_limit == 30
    assert len(bot.handlers) == 2
    assert isinstance(bot.handlers[0], LoggingHandler)
    assert isinstance(bot.handlers[1], EchoHandler)
