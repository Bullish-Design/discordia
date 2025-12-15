# src/discordia/persistence/jsonl.py
from __future__ import annotations

import json
from typing import Any

import aiofiles  # type: ignore[import-untyped]
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

            async with aiofiles.open(self.filepath, mode="a", encoding="utf-8") as f:
                await f.write(line + "\n")
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
            entries: list[dict[str, Any]] = []
            async with aiofiles.open(self.filepath, mode="r", encoding="utf-8") as f:
                async for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    entries.append(json.loads(stripped))
            return entries
        except FileNotFoundError:
            return []
        except Exception as e:
            raise JSONLError("Failed to read JSONL file", cause=e) from e


__all__ = ["JSONLWriter"]
