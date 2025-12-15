# src/discordia/persistence/jsonl.py
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from pydantic import BaseModel

from discordia.exceptions import JSONLError

logger = logging.getLogger("discordia.persistence.jsonl")


class JSONLBackend:
    """JSONL persistence backend."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    async def write(self, entity: BaseModel, entity_type: str) -> None:
        """Append entity to JSONL file."""
        try:
            data = json.loads(entity.model_dump_json())
            entry: dict[str, Any] = {"type": entity_type, "data": data}
            line = json.dumps(entry, separators=(",", ":"), ensure_ascii=False)
            await asyncio.to_thread(self._append_line, line)
            logger.debug("Wrote %s to JSONL", entity_type)
        except Exception as e:
            logger.error("Failed to write to JSONL: %s", e, exc_info=True)
            raise JSONLError(f"Failed to write {entity_type} to JSONL", cause=e) from e

    def _append_line(self, line: str) -> None:
        """Synchronous file append."""
        with open(self.filepath, mode="a", encoding="utf-8") as f:
            f.write(line + "\n")

    async def read_all(self) -> list[dict[str, Any]]:
        """Read all JSONL entries."""
        try:
            return await asyncio.to_thread(self._read_all_lines)
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error("Failed to read JSONL: %s", e, exc_info=True)
            raise JSONLError("Failed to read JSONL file", cause=e) from e

    def _read_all_lines(self) -> list[dict[str, Any]]:
        """Synchronous file read."""
        entries: list[dict[str, Any]] = []
        with open(self.filepath, mode="r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    entries.append(json.loads(stripped))
        return entries


__all__ = ["JSONLBackend"]
