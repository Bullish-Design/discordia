# examples/llm_handlers/pygentic_adapter.py
"""Async adapter for PyGentic LLM calls."""
from __future__ import annotations

import asyncio
from functools import partial
from typing import Any, TypeVar

T = TypeVar("T")


class LLMError(Exception):
    """Base exception for LLM operations."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.message = message
        self.cause = cause
        super().__init__(message)


class LLMAPIError(LLMError):
    """Raised when an LLM API call fails."""


class ContextTooLargeError(LLMError):
    """Raised when LLM context exceeds model limits."""


async def generate_async(model_class: type[T], **kwargs: Any) -> T:
    """Create GenModel instance asynchronously to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, partial(model_class, **kwargs))
    except Exception as e:
        error_msg = str(e).lower()
        if any(term in error_msg for term in ("context", "token", "length")):
            raise ContextTooLargeError("PyGentic context exceeded limits", cause=e) from e
        raise LLMAPIError("PyGentic generation failed", cause=e) from e


async def access_property_async(instance: Any, property_name: str) -> Any:
    """Access a generated_property asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: getattr(instance, property_name))


__all__ = ["generate_async", "access_property_async", "LLMError", "LLMAPIError", "ContextTooLargeError"]
