# tests/test_llm.py
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from discordia.exceptions import ContextTooLargeError, LLMAPIError
from discordia.llm.client import LLMClient
from discordia.models.message import DiscordMessage


@pytest.fixture
def llm_client() -> LLMClient:
    """Create an LLM client for testing."""

    return LLMClient(api_key="test-key", model="test-model")


@pytest.fixture
def sample_messages() -> list[DiscordMessage]:
    """Create sample messages for testing."""

    now = datetime.utcnow()
    return [
        DiscordMessage(id=1, content="Hello!", author_id=100, channel_id=200, timestamp=now),
        DiscordMessage(id=2, content="How are you?", author_id=100, channel_id=200, timestamp=now),
    ]


def test_llm_client_initialization() -> None:
    """LLM client initializes with API key and model."""

    client = LLMClient(api_key="k", model="m")
    assert client.api_key == "k"
    assert client.model == "m"


def test_format_messages_for_llm(llm_client: LLMClient, sample_messages: list[DiscordMessage]) -> None:
    """_format_messages_for_llm converts to provider format."""

    formatted = llm_client._format_messages_for_llm(sample_messages)
    assert formatted == [
        {"role": "user", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]


@pytest.mark.asyncio
async def test_generate_response_with_no_context(llm_client: LLMClient) -> None:
    """generate_response handles empty context gracefully."""

    response = await llm_client.generate_response([])
    assert "no context" in response.lower()


@pytest.mark.asyncio
async def test_generate_response_calls_provider(llm_client: LLMClient, sample_messages: list[DiscordMessage]) -> None:
    """generate_response calls provider with formatted messages."""

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    llm_client._call_provider = AsyncMock(return_value=mock_response)  # type: ignore[method-assign]

    result = await llm_client.generate_response(sample_messages)
    assert result == "Test response"

    llm_client._call_provider.assert_awaited_once()
    args, kwargs = llm_client._call_provider.call_args
    assert args[0] == [
        {"role": "user", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]
    assert kwargs["max_tokens"] == 1024
    assert "helpful" in kwargs["system_prompt"].lower()


@pytest.mark.asyncio
async def test_generate_response_error_handling(llm_client: LLMClient, sample_messages: list[DiscordMessage]) -> None:
    """generate_response wraps exceptions in LLMAPIError."""

    llm_client._call_provider = AsyncMock(side_effect=RuntimeError("API down"))  # type: ignore[method-assign]

    with pytest.raises(LLMAPIError) as exc_info:
        await llm_client.generate_response(sample_messages)

    assert "Failed to generate" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_response_context_too_large(
    llm_client: LLMClient,
    sample_messages: list[DiscordMessage],
) -> None:
    """Context-related failures raise ContextTooLargeError."""

    llm_client._call_provider = AsyncMock(  # type: ignore[method-assign]
        side_effect=RuntimeError("Context length exceeded")
    )

    with pytest.raises(ContextTooLargeError):
        await llm_client.generate_response(sample_messages)


@pytest.mark.asyncio
async def test_summarize_calls_generate_response(
    llm_client: LLMClient,
    sample_messages: list[DiscordMessage],
) -> None:
    """summarize delegates to generate_response with a summarization system prompt."""

    llm_client.generate_response = AsyncMock(return_value="Summary")  # type: ignore[method-assign]
    result = await llm_client.summarize(sample_messages)
    assert result == "Summary"
    llm_client.generate_response.assert_awaited_once()
    _, kwargs = llm_client.generate_response.call_args
    assert "summarize" in str(kwargs["system_prompt"]).lower()
