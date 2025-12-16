# tests/test_context.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from discordia.context import MessageContext
from discordia.state import Channel, MemoryState, Message, User


def create_context(content: str, **kwargs: object) -> MessageContext:
    state = MemoryState()
    user = User(id=111, username="Alice")
    channel = Channel(id=789, name="general", server_id=456)

    timestamp = kwargs.pop("timestamp", datetime.now(UTC))

    return MessageContext(
        message_id=999,
        content=content,
        author=user,
        channel=channel,
        store=state,
        timestamp=timestamp,
        **kwargs,
    )


def test_is_command_true() -> None:
    ctx = create_context("!ping")
    assert ctx.is_command is True


def test_is_command_false() -> None:
    ctx = create_context("Hello world")
    assert ctx.is_command is False


def test_command_parts() -> None:
    ctx = create_context("!echo hello world")
    assert ctx.command_parts == ["!echo", "hello", "world"]


def test_command_name() -> None:
    ctx = create_context("!ping")
    assert ctx.command_name == "ping"


def test_command_name_none() -> None:
    ctx = create_context("Hello")
    assert ctx.command_name is None


def test_command_args() -> None:
    ctx = create_context("!echo hello world")
    assert ctx.command_args == ["hello", "world"]


def test_command_args_empty() -> None:
    ctx = create_context("!ping")
    assert ctx.command_args == []


def test_age_ms() -> None:
    past = datetime.now(UTC) - timedelta(seconds=2)
    ctx = create_context("test", timestamp=past)
    assert ctx.age_ms >= 2000


def test_mentions_bot_true() -> None:
    ctx = create_context("Hey <@123> check this")
    assert ctx.mentions_bot is True


def test_mentions_bot_false() -> None:
    ctx = create_context("Hello world")
    assert ctx.mentions_bot is False


@pytest.mark.asyncio
async def test_get_history() -> None:
    state = MemoryState()

    user = User(id=111, username="Alice")
    await state.save_user(user)

    channel = Channel(id=789, name="general", server_id=456)
    await state.save_channel(channel)

    now = datetime.now(UTC)
    for i in range(5):
        msg = Message(
            id=1000 + i,
            content=f"Msg {i}",
            author_id=111,
            channel_id=789,
            timestamp=now + timedelta(milliseconds=i),
        )
        await state.save_message(msg)

    ctx = MessageContext(
        message_id=1005,
        content="current",
        author=user,
        channel=channel,
        store=state,
        timestamp=datetime.now(UTC),
    )

    history = await ctx.get_history(limit=3)
    assert len(history) == 3
