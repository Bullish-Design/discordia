# src/discordia/handlers/pygentic_adapter.py
from __future__ import annotations

import asyncio
from functools import partial
from typing import Any, TypeVar

from discordia.exceptions import ContextTooLargeError, LLMAPIError

T = TypeVar("T")


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


__all__ = ["generate_async", "access_property_async"]
