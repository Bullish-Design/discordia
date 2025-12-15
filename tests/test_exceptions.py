# tests/test_exceptions.py
from __future__ import annotations

from typing import Type

from pydantic import ValidationError as PydanticValidationError

from discordia.exceptions import (
    CategoryNotFoundError,
    ChannelNotFoundError,
    ConfigurationError,
    ContextTooLargeError,
    DatabaseError,
    DiscordAPIError,
    DiscordiaError,
    JSONLError,
    LLMAPIError,
    LLMError,
    MessageSendError,
    PersistenceError,
    ValidationError,
)


def _all_discordia_exceptions() -> list[Type[Exception]]:
    return [
        DiscordiaError,
        ConfigurationError,
        DiscordAPIError,
        ChannelNotFoundError,
        CategoryNotFoundError,
        MessageSendError,
        PersistenceError,
        DatabaseError,
        JSONLError,
        LLMError,
        LLMAPIError,
        ContextTooLargeError,
    ]


def test_base_exception_with_message_only() -> None:
    """Base exception works with just a message."""
    error = DiscordiaError("Something went wrong")
    assert str(error) == "Something went wrong"
    assert error.message == "Something went wrong"
    assert error.cause is None


def test_base_exception_with_cause() -> None:
    """Base exception includes cause in string representation."""
    cause = ValueError("Original error")
    error = DiscordiaError("Something went wrong", cause=cause)
    rendered = str(error)
    assert "Something went wrong" in rendered
    assert "Original error" in rendered
    assert error.cause is cause


def test_exception_hierarchy() -> None:
    """Exception inheritance is correct."""
    assert issubclass(ConfigurationError, DiscordiaError)
    assert issubclass(DiscordAPIError, DiscordiaError)
    assert issubclass(ChannelNotFoundError, DiscordAPIError)
    assert issubclass(CategoryNotFoundError, DiscordAPIError)
    assert issubclass(MessageSendError, DiscordAPIError)
    assert issubclass(PersistenceError, DiscordiaError)
    assert issubclass(DatabaseError, PersistenceError)
    assert issubclass(JSONLError, PersistenceError)
    assert issubclass(LLMError, DiscordiaError)
    assert issubclass(LLMAPIError, LLMError)
    assert issubclass(ContextTooLargeError, LLMError)


def test_all_exceptions_can_be_instantiated_with_message_only() -> None:
    """Every custom exception supports a message-only constructor."""
    for exc_type in _all_discordia_exceptions():
        exc = exc_type("message")
        assert isinstance(exc, exc_type)
        assert str(exc) == "message"
        assert getattr(exc, "cause") is None


def test_all_exceptions_can_be_instantiated_with_cause() -> None:
    """Every custom exception supports message + cause."""
    cause = RuntimeError("boom")
    for exc_type in _all_discordia_exceptions():
        exc = exc_type("message", cause=cause)
        assert isinstance(exc, exc_type)
        assert exc.cause is cause
        assert "boom" in str(exc)


def test_str_representation_without_cause_does_not_include_cause_marker() -> None:
    """__str__ should not mention causes when absent."""
    exc = DatabaseError("db failed")
    assert str(exc) == "db failed"
    assert "caused by" not in str(exc).lower()


def test_str_representation_with_cause_includes_cause_marker() -> None:
    """__str__ should mention causes when present."""
    exc = DatabaseError("db failed", cause=ValueError("bad sql"))
    rendered = str(exc).lower()
    assert "db failed" in rendered
    assert "caused by" in rendered
    assert "bad sql" in rendered


def test_all_custom_exceptions_have_docstrings() -> None:
    """All custom exception types must be documented."""
    for exc_type in _all_discordia_exceptions():
        doc = exc_type.__doc__
        assert doc is not None
        assert doc.strip() != ""


def test_validation_error_is_reexported_from_pydantic() -> None:
    """ValidationError is reexported for convenience."""
    assert ValidationError is PydanticValidationError
