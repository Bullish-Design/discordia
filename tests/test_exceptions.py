# tests/test_exceptions.py
from __future__ import annotations

import pytest

from discordia.exceptions import (
    CategoryNotFoundError,
    ChannelNotFoundError,
    ConfigurationError,
    ContextTooLargeError,
    DatabaseError,
    DiscordAPIError,
    DiscordiaError,
    HandlerError,
    JSONLError,
    LLMAPIError,
    LLMError,
    MessageSendError,
    PersistenceError,
    ReconciliationError,
    StateError,
    TemplateError,
)


def test_base_exception_default_message():
    """DiscordiaError derives default message from class name."""
    error = DiscordiaError()
    assert error.message == "Discordia Error"
    assert str(error) == "Discordia Error"


def test_base_exception_custom_message():
    """DiscordiaError accepts custom message."""
    error = DiscordiaError("Custom error message")
    assert error.message == "Custom error message"
    assert str(error) == "Custom error message"


def test_base_exception_with_cause():
    """DiscordiaError can wrap another exception."""
    cause = ValueError("Original error")
    error = DiscordiaError("Wrapper error", cause=cause)
    assert error.message == "Wrapper error"
    assert error.cause is cause
    assert str(error) == "Wrapper error (caused by: Original error)"


def test_configuration_error():
    """ConfigurationError is a DiscordiaError."""
    error = ConfigurationError("Invalid config")
    assert isinstance(error, DiscordiaError)
    assert error.message == "Invalid config"


def test_discord_api_error():
    """DiscordAPIError is a DiscordiaError."""
    error = DiscordAPIError("API request failed")
    assert isinstance(error, DiscordiaError)
    assert error.message == "API request failed"


def test_channel_not_found_error():
    """ChannelNotFoundError is a DiscordAPIError."""
    error = ChannelNotFoundError("Channel not found")
    assert isinstance(error, DiscordAPIError)
    assert isinstance(error, DiscordiaError)


def test_category_not_found_error():
    """CategoryNotFoundError is a DiscordAPIError."""
    error = CategoryNotFoundError()
    assert isinstance(error, DiscordAPIError)
    assert error.message == "Category Not Found Error"


def test_message_send_error():
    """MessageSendError is a DiscordAPIError."""
    error = MessageSendError("Failed to send")
    assert isinstance(error, DiscordAPIError)


def test_persistence_error():
    """PersistenceError is a DiscordiaError."""
    error = PersistenceError("Storage failed")
    assert isinstance(error, DiscordiaError)


def test_database_error():
    """DatabaseError is a PersistenceError."""
    error = DatabaseError("DB connection failed")
    assert isinstance(error, PersistenceError)


def test_jsonl_error():
    """JSONLError is a PersistenceError."""
    error = JSONLError("Failed to write JSONL")
    assert isinstance(error, PersistenceError)


def test_llm_error():
    """LLMError is a DiscordiaError."""
    error = LLMError("LLM request failed")
    assert isinstance(error, DiscordiaError)


def test_llm_api_error():
    """LLMAPIError is an LLMError."""
    error = LLMAPIError("API call failed")
    assert isinstance(error, LLMError)


def test_context_too_large_error():
    """ContextTooLargeError is an LLMError."""
    error = ContextTooLargeError("Context exceeds limit")
    assert isinstance(error, LLMError)


def test_template_error():
    """TemplateError is a DiscordiaError."""
    error = TemplateError("Invalid template")
    assert isinstance(error, DiscordiaError)


def test_reconciliation_error():
    """ReconciliationError is a DiscordiaError."""
    error = ReconciliationError("Reconciliation failed")
    assert isinstance(error, DiscordiaError)


def test_state_error():
    """StateError is a DiscordiaError."""
    error = StateError("State operation failed")
    assert isinstance(error, DiscordiaError)


def test_handler_error():
    """HandlerError is a DiscordiaError."""
    error = HandlerError("Handler execution failed")
    assert isinstance(error, DiscordiaError)


def test_exception_hierarchy():
    """Verify exception inheritance chain."""
    error = ChannelNotFoundError("test")
    assert isinstance(error, ChannelNotFoundError)
    assert isinstance(error, DiscordAPIError)
    assert isinstance(error, DiscordiaError)
    assert isinstance(error, Exception)
