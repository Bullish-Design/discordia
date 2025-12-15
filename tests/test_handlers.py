# tests/test_handlers.py
from __future__ import annotations

from datetime import datetime

import pytest

from discordia.engine.context import MessageContext
from discordia.handlers.logging import LoggingHandler
from discordia.handlers.router import HandlerRouter
from discordia.state.memory import MemoryState
from discordia.state.models import Channel, User


class MockHandler:
    """Mock handler for testing."""

    def __init__(self, can_handle_result: bool = True, response: str | None = "mock response"):
        self.can_handle_result = can_handle_result
        self.response = response
        self.can_handle_called = False
        self.handle_called = False

    async def can_handle(self, ctx: MessageContext) -> bool:
        self.can_handle_called = True
        return self.can_handle_result

    async def handle(self, ctx: MessageContext) -> str | None:
        self.handle_called = True
        return self.response


@pytest.fixture
async def message_context() -> MessageContext:
    """Create test message context."""
    state = MemoryState()
    user = User(id=123456789012345678, username="TestUser")
    await state.save_user(user)

    channel = Channel(
        id=987654321098765432,
        name="test-channel",
        server_id=111222333444555666,
        topic="Test topic",
    )
    await state.save_channel(channel)

    return MessageContext(
        message_id=555666777888999000,
        content="Test message",
        author_id=user.id,
        author_name=user.username,
        channel_id=channel.id,
        channel_name=channel.name,
        channel=channel,
        author=user,
        store=state,
    )


@pytest.mark.asyncio
async def test_logging_handler_can_handle(message_context):
    """LoggingHandler handles all messages."""
    handler = LoggingHandler()
    assert await handler.can_handle(message_context) is True


@pytest.mark.asyncio
async def test_logging_handler_returns_none(message_context):
    """LoggingHandler returns None (no response)."""
    handler = LoggingHandler()
    result = await handler.handle(message_context)
    assert result is None


@pytest.mark.asyncio
async def test_router_with_single_handler(message_context):
    """Router routes to first matching handler."""
    handler = MockHandler()
    router = HandlerRouter([handler])

    result = await router.route(message_context)

    assert handler.can_handle_called
    assert handler.handle_called
    assert result == "mock response"


@pytest.mark.asyncio
async def test_router_with_multiple_handlers(message_context):
    """Router stops at first handler that can handle."""
    handler1 = MockHandler(can_handle_result=False)
    handler2 = MockHandler(can_handle_result=True, response="second")
    handler3 = MockHandler(can_handle_result=True, response="third")

    router = HandlerRouter([handler1, handler2, handler3])
    result = await router.route(message_context)

    assert handler1.can_handle_called
    assert not handler1.handle_called
    assert handler2.can_handle_called
    assert handler2.handle_called
    assert not handler3.can_handle_called
    assert result == "second"


@pytest.mark.asyncio
async def test_router_no_matching_handler(message_context):
    """Router returns None if no handler matches."""
    handler1 = MockHandler(can_handle_result=False)
    handler2 = MockHandler(can_handle_result=False)

    router = HandlerRouter([handler1, handler2])
    result = await router.route(message_context)

    assert result is None


@pytest.mark.asyncio
async def test_router_empty_handlers(message_context):
    """Router with no handlers returns None."""
    router = HandlerRouter([])
    result = await router.route(message_context)
    assert result is None


@pytest.mark.asyncio
async def test_router_handler_exception(message_context, caplog):
    """Router continues if handler raises exception."""

    class FailingHandler:
        async def can_handle(self, ctx: MessageContext) -> bool:
            return True

        async def handle(self, ctx: MessageContext) -> str | None:
            raise ValueError("Handler failed")

    handler1 = FailingHandler()
    handler2 = MockHandler(response="fallback")

    router = HandlerRouter([handler1, handler2])
    result = await router.route(message_context)

    assert result is "fallback" #None


@pytest.mark.asyncio
async def test_message_context_get_history():
    """MessageContext can retrieve message history."""
    state = MemoryState()
    user = User(id=123456789012345678, username="TestUser")
    await state.save_user(user)

    channel = Channel(
        id=987654321098765432,
        name="test-channel",
        server_id=111222333444555666,
    )
    await state.save_channel(channel)

    from discordia.state.models import Message

    base_time = datetime.utcnow()
    for i in range(5):
        message = Message(
            id=555666777888999000 + i,
            content=f"Message {i}",
            author_id=user.id,
            channel_id=channel.id,
            timestamp=base_time,
        )
        await state.save_message(message)

    ctx = MessageContext(
        message_id=555666777888999999,
        content="Current message",
        author_id=user.id,
        author_name=user.username,
        channel_id=channel.id,
        channel_name=channel.name,
        channel=channel,
        author=user,
        store=state,
    )

    history = await ctx.get_history(limit=3)
    assert len(history) == 3
    assert history[-1].content == "Message 4"
