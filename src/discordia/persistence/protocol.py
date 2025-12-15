# src/discordia/persistence/protocol.py
from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


@runtime_checkable
class PersistenceBackend(Protocol):
    """Protocol for long-term persistence backends."""

    async def write(self, entity: BaseModel, entity_type: str) -> None:
        """Persist an entity."""
        ...

    async def read_all(self) -> list[dict[str, any]]:
        """Read all persisted entities."""
        ...


__all__ = ["PersistenceBackend"]
