# src/discordia/persistence/jsonl.py
from __future__ import annotations

import asyncio
import json
from typing import Any
from pydantic import BaseModel

from discordia.exceptions import JSONLError
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser


class JSONLWriter:
    """Async JSONL writer for Discord entity backup logging.

    Writes append-only, one JSON object per line, and includes a type identifier so the log can be
    replayed or inspected easily.
    """

    filepath: str

    def __init__(self, filepath: str) -> None:
        """Initialize JSONL writer.

        Args:
            filepath: Path to JSONL file (created if it does not exist)
        """

        self.filepath = filepath

    async def write(self, entity: BaseModel, entity_type: str) -> None:
        """Write an entity to the JSONL file.

        Args:
            entity: Pydantic/SQLModel model instance to serialize
            entity_type: Type identifier (e.g., "category", "message")

        Raises:
            JSONLError: If write operation fails
        """

        try:
            # Use model_dump_json to ensure datetimes and other values are serialized in a JSON-safe
            # form. Then wrap with type metadata.
            data = json.loads(entity.model_dump_json())
            entry: dict[str, Any] = {"type": entity_type, "data": data}
            line = json.dumps(entry, separators=(",", ":"), ensure_ascii=False)

            await asyncio.to_thread(_append_line, self.filepath, line)
        except Exception as e:
            raise JSONLError(f"Failed to write {entity_type} to JSONL", cause=e) from e

    async def write_category(self, category: DiscordCategory) -> None:
        """Write a category entry."""

        await self.write(category, "category")

    async def write_channel(self, channel: DiscordTextChannel) -> None:
        """Write a channel entry."""

        await self.write(channel, "channel")

    async def write_message(self, message: DiscordMessage) -> None:
        """Write a message entry."""

        await self.write(message, "message")

    async def write_user(self, user: DiscordUser) -> None:
        """Write a user entry."""

        await self.write(user, "user")

    async def read_all(self) -> list[dict[str, Any]]:
        """Read all entries from the JSONL file.

        Returns:
            Parsed JSON entries.

        Raises:
            JSONLError: If reading/parsing fails (except missing file, which returns []).
        """

        try:
            return await asyncio.to_thread(_read_all_lines, self.filepath)
        except FileNotFoundError:
            return []
        except Exception as e:
            raise JSONLError("Failed to read JSONL file", cause=e) from e


def _append_line(filepath: str, line: str) -> None:
    with open(filepath, mode="a", encoding="utf-8") as f:
        f.write(line + "\n")


def _read_all_lines(filepath: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            entries.append(json.loads(stripped))
    return entries


__all__ = ["JSONLWriter"]
