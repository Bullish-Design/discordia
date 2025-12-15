# tests/test_pygentic_adapter.py
from __future__ import annotations

import pytest

from discordia.exceptions import ContextTooLargeError, LLMAPIError
from discordia.handlers.pygentic_adapter import access_property_async, generate_async


class MockGenModel:
    """Mock PyGentic model for testing."""

    def __init__(self, value: str = "test"):
        self.value = value
        self._generated_property = "generated value"

    @property
    def generated_property(self) -> str:
        return self._generated_property


class FailingModel:
    """Model that raises on creation."""

    def __init__(self, **kwargs):
        raise ValueError("Model creation failed")


class ContextErrorModel:
    """Model that raises context-related error."""

    def __init__(self, **kwargs):
        raise ValueError("Context length exceeded maximum token limit")


@pytest.mark.asyncio
async def test_generate_async_success():
    """generate_async creates model instance asynchronously."""
    instance = await generate_async(MockGenModel, value="test_value")
    assert isinstance(instance, MockGenModel)
    assert instance.value == "test_value"


@pytest.mark.asyncio
async def test_generate_async_with_kwargs():
    """generate_async passes kwargs to model constructor."""
    instance = await generate_async(MockGenModel, value="custom")
    assert instance.value == "custom"


@pytest.mark.asyncio
async def test_generate_async_failure():
    """generate_async raises LLMAPIError on failure."""
    with pytest.raises(LLMAPIError, match="PyGentic generation failed"):
        await generate_async(FailingModel)


@pytest.mark.asyncio
async def test_generate_async_context_error():
    """generate_async raises ContextTooLargeError for context issues."""
    with pytest.raises(ContextTooLargeError, match="context exceeded limits"):
        await generate_async(ContextErrorModel)


@pytest.mark.asyncio
async def test_access_property_async_success():
    """access_property_async retrieves property asynchronously."""
    instance = MockGenModel()
    value = await access_property_async(instance, "value")
    assert value == "test"


@pytest.mark.asyncio
async def test_access_property_async_generated():
    """access_property_async works with generated properties."""
    instance = MockGenModel()
    value = await access_property_async(instance, "generated_property")
    assert value == "generated value"


@pytest.mark.asyncio
async def test_access_property_async_nonexistent():
    """access_property_async raises for nonexistent property."""
    instance = MockGenModel()
    with pytest.raises(AttributeError):
        await access_property_async(instance, "nonexistent")
