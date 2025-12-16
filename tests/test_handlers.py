# tests/test_handlers.py
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from discordia.context import MessageContext
from discordia.handlers import EchoConfig, EchoHandler, LoggingConfig, LoggingHandler
from discordia.state import Channel, MemoryState, User


def create_context(content: str) -> MessageContext:
    return MessageContext(
        message_id=999,
        content=content,
        author=User(id=111, username="Alice"),
        channel=Channel(id=789, name="general", server_id=456),
        store=MemoryState(),
        timestamp=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_logging_handler_can_handle() -> None:
    handler = LoggingHandler()
    ctx = create_context("test")
    assert await handler.can_handle(ctx) is True


@pytest.mark.asyncio
async def test_logging_handler_disabled() -> None:
    handler = LoggingHandler(config=LoggingConfig(enabled=False))
    ctx = create_context("test")
    assert await handler.can_handle(ctx) is False


@pytest.mark.asyncio
async def test_logging_handler_returns_none() -> None:
    handler = LoggingHandler()
    ctx = create_context("test")
    response = await handler.handle(ctx)
    assert response is None


@pytest.mark.asyncio
async def test_echo_handler_matches() -> None:
    handler = EchoHandler()
    ctx = create_context("echo:hello world")
    assert await handler.can_handle(ctx) is True


@pytest.mark.asyncio
async def test_echo_handler_no_match() -> None:
    handler = EchoHandler()
    ctx = create_context("hello world")
    assert await handler.can_handle(ctx) is False


@pytest.mark.asyncio
async def test_echo_handler_response() -> None:
    handler = EchoHandler()
    ctx = create_context("echo:hello world")
    response = await handler.handle(ctx)
    assert response == "hello world"


@pytest.mark.asyncio
async def test_echo_handler_custom_prefix() -> None:
    handler = EchoHandler(config=EchoConfig(prefix="repeat:"))
    ctx = create_context("repeat:test")
    assert await handler.can_handle(ctx) is True
    response = await handler.handle(ctx)
    assert response == "test"


def test_handler_generic_config() -> None:
    handler = EchoHandler()
    assert isinstance(handler.config, EchoConfig)
    assert handler.config.prefix == "echo:"