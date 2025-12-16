# tests/test_bot.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable

import pytest
from pydantic import SecretStr

from discordia.bot import Bot
from discordia.config import BotConfig
from discordia.handlers import EchoConfig, EchoHandler


@dataclass
class DummyUser:
    id: int
    username: str
    bot: bool = False


@dataclass
class DummyChannel:
    id: int
    name: str
    parent_id: int | None = None
    topic: str | None = None


@dataclass
class DummyMessage:
    id: int
    content: str
    author: DummyUser
    channel: DummyChannel
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    reply_calls: list[str] = field(default_factory=list)
    reply_return: Any = None

    async def reply(self, content: str) -> Any:
        self.reply_calls.append(content)
        if self.reply_return is None:
            self.reply_return = DummyMessage(
                id=self.id + 1000,
                content=content,
                author=DummyUser(id=999, username="Bot", bot=True),
                channel=self.channel,
            )
        return self.reply_return


@dataclass
class DummyMessageCreateEvent:
    message: DummyMessage


@dataclass
class DummyReadyEvent:
    user: DummyUser


@dataclass
class DummyClient:
    user: DummyUser
    listeners: list[Any] = field(default_factory=list)
    fetch_guild_impl: Callable[[int], Any] | None = None

    def add_listener(self, listener: Any) -> None:
        self.listeners.append(listener)

    async def fetch_guild(self, guild_id: int) -> Any:
        if not self.fetch_guild_impl:
            raise RuntimeError("fetch_guild not configured")
        return self.fetch_guild_impl(guild_id)

    def start(self) -> None:  # pragma: no cover
        raise RuntimeError("Dummy client cannot start")

    async def stop(self) -> None:  # pragma: no cover
        return None


class _PluginProbe:
    def __init__(self) -> None:
        self.ready_calls = 0
        self.message_calls = 0

    async def on_ready(self, bot: Any, guild: Any) -> None:
        self.ready_calls += 1

    async def on_message(self, bot: Any, ctx: Any) -> None:
        self.message_calls += 1


def _config() -> BotConfig:
    return BotConfig(discord_token=SecretStr("test"), server_id=123456789)


def test_bot_initialization_registers_listeners() -> None:
    client = DummyClient(user=DummyUser(id=999, username="Bot", bot=True))
    bot = Bot(config=_config(), client=client)

    assert bot.config.server_id == 123456789
    assert bot.client is client
    assert len(client.listeners) == 2


@pytest.mark.asyncio
async def test_bot_on_ready_discovers_and_calls_plugins() -> None:
    plugin = _PluginProbe()

    guild = type("Guild", (), {"channels": []})()
    client = DummyClient(
        user=DummyUser(id=999, username="Bot", bot=True),
        fetch_guild_impl=lambda guild_id: guild,
    )
    bot = Bot(config=_config(), client=client, plugins=[plugin])

    await bot._on_ready(DummyReadyEvent(user=client.user))

    assert plugin.ready_calls == 1


@pytest.mark.asyncio
async def test_bot_ignores_bot_messages() -> None:
    plugin = _PluginProbe()
    client = DummyClient(user=DummyUser(id=999, username="Bot", bot=True))
    bot = Bot(config=_config(), client=client, plugins=[plugin])

    message = DummyMessage(
        id=1,
        content="echo: hello",
        author=DummyUser(id=2, username="OtherBot", bot=True),
        channel=DummyChannel(id=10, name="general"),
    )

    await bot._on_message(DummyMessageCreateEvent(message=message))

    assert plugin.message_calls == 0
    assert message.reply_calls == []


@pytest.mark.asyncio
async def test_bot_routes_to_first_matching_handler_and_replies() -> None:
    plugin = _PluginProbe()
    client = DummyClient(user=DummyUser(id=999, username="Bot", bot=True))

    handler = EchoHandler(config=EchoConfig(prefix="echo:"))
    bot = Bot(config=_config(), client=client, handlers=[handler], plugins=[plugin])

    message = DummyMessage(
        id=100,
        content="echo: hello world",
        author=DummyUser(id=2, username="Alice"),
        channel=DummyChannel(id=10, name="general"),
    )

    await bot._on_message(DummyMessageCreateEvent(message=message))

    assert plugin.message_calls == 1
    assert message.reply_calls == ["hello world"]

    # State should include the inbound message and the bot reply.
    messages = list(bot.state.messages.values())
    assert any(m.content == "echo: hello world" for m in messages)
    assert any(m.content == "hello world" for m in messages)
