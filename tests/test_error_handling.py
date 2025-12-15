# tests/test_error_handling.py
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.exceptions import ContextTooLargeError, DatabaseError, LLMAPIError
from discordia.managers.message_handler import MessageHandler
from discordia.models.message import DiscordMessage


@pytest.fixture
def message_handler() -> MessageHandler:
    """Create a MessageHandler wired with mocks."""

    mock_db = MagicMock()
    mock_db.save_user = AsyncMock()
    mock_db.save_message = AsyncMock()
    mock_db.get_messages = AsyncMock(return_value=[])

    mock_jsonl = MagicMock()
    mock_jsonl.write_user = AsyncMock()
    mock_jsonl.write_message = AsyncMock()

    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(return_value="Response")

    mock_channel_manager = MagicMock()
    mock_channel_manager.is_log_channel = MagicMock(return_value=True)

    return MessageHandler(
        db=mock_db,
        jsonl=mock_jsonl,
        llm_client=mock_llm,
        channel_manager=mock_channel_manager,
        context_limit=20,
        max_message_length=2000,
    )


def _mock_context_message() -> DiscordMessage:
    return DiscordMessage(
        id=1,
        content="Previous message",
        author_id=100,
        channel_id=200,
        timestamp=datetime.utcnow(),
    )


def _create_mock_message() -> MagicMock:
    mock = MagicMock()
    mock.id = 999
    mock.content = "Test"
    mock.author.id = 100
    mock.author.username = "user"
    mock.author.bot = False
    mock.channel.id = 200
    mock.timestamp = datetime.utcnow()
    mock.edited_timestamp = None

    mock_channel = MagicMock()
    mock_channel.name = "2024-12-14"
    mock.channel.fetch = AsyncMock(return_value=mock_channel)

    mock.reply = AsyncMock(return_value=MagicMock())
    return mock


@pytest.mark.asyncio
async def test_handle_message_db_failure_continues(message_handler: MessageHandler) -> None:
    """Message processing continues even if DB save fails."""

    message_handler.db.save_message = AsyncMock(side_effect=DatabaseError("DB Error"))

    mock_message = _create_mock_message()
    message_handler.db.get_messages = AsyncMock(return_value=[_mock_context_message()])
    message_handler.llm_client.generate_response = AsyncMock(return_value="Response")

    await message_handler.handle_message(mock_message)

    message_handler.llm_client.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_llm_failure_notifies_user(message_handler: MessageHandler) -> None:
    """LLM failure sends error message to user."""

    message_handler.llm_client.generate_response = AsyncMock(side_effect=LLMAPIError("API Error"))
    mock_message = _create_mock_message()
    message_handler.db.get_messages = AsyncMock(return_value=[_mock_context_message()])

    await message_handler.handle_message(mock_message)

    assert mock_message.reply.called
    reply_content = str(mock_message.reply.call_args[0][0])
    assert "⚠️" in reply_content


@pytest.mark.asyncio
async def test_handle_message_context_too_large_notifies_user(message_handler: MessageHandler) -> None:
    """ContextTooLargeError sends a helpful message to the user."""

    message_handler.llm_client.generate_response = AsyncMock(side_effect=ContextTooLargeError("Too big"))
    mock_message = _create_mock_message()
    message_handler.db.get_messages = AsyncMock(return_value=[_mock_context_message()])

    await message_handler.handle_message(mock_message)

    assert mock_message.reply.called
    reply_content = str(mock_message.reply.call_args[0][0])
    assert "too long" in reply_content.lower() or "too large" in reply_content.lower()


@pytest.mark.asyncio
async def test_handle_message_send_failure_retries(message_handler: MessageHandler) -> None:
    """Failed message send retries once."""

    mock_message = _create_mock_message()
    mock_message.reply = AsyncMock(side_effect=[Exception("Network error"), MagicMock()])
    message_handler.db.get_messages = AsyncMock(return_value=[_mock_context_message()])
    message_handler.llm_client.generate_response = AsyncMock(return_value="Response")

    with patch("discordia.managers.message_handler.asyncio.sleep", new=AsyncMock()) as _sleep:
        await message_handler.handle_message(mock_message)

    assert mock_message.reply.call_count >= 2
