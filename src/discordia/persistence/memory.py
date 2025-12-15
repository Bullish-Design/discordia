# src/discordia/persistence/memory.py
from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("discordia.persistence.memory")


class MemoryBackend:
    """In-memory persistence backend for testing."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def write(self, entity: BaseModel, entity_type: str) -> None:
        """Store entity in memory."""
        data = entity.model_dump()
        entry = {"type": entity_type, "data": data}
        self.entries.append(entry)
        logger.debug("Stored %s in memory", entity_type)

    async def read_all(self) -> list[dict[str, Any]]:
        """Return all stored entries."""
        return self.entries.copy()


__all__ = ["MemoryBackend"]
