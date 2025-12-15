# src/discordia/managers/category_manager.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discordia.exceptions import CategoryNotFoundError, DiscordAPIError
from discordia.models.category import DiscordCategory

if TYPE_CHECKING:
    from discordia.persistence.database import DatabaseWriter
    from discordia.persistence.jsonl import JSONLWriter

logger = logging.getLogger("discordia.category_manager")


try:  # pragma: no cover
    from interactions.models.discord.channel import GuildCategory as GuildCategory
except Exception:  # pragma: no cover
    # Allows unit tests to run without importing interactions internals.
    class GuildCategory:  # type: ignore[no-redef]
        """Fallback GuildCategory type for runtime imports."""


class CategoryManager:
    """Manages Discord category discovery and persistence."""

    def __init__(self, db: DatabaseWriter, jsonl: JSONLWriter, server_id: int) -> None:
        """Initialize category manager.

        Args:
            db: Database writer for persistence
            jsonl: JSONL writer for backup
            server_id: Discord server (guild) ID
        """

        self.db = db
        self.jsonl = jsonl
        self.server_id = server_id

    async def discover_categories(self, guild: Any) -> list[DiscordCategory]:
        """Discover all categories in a guild.

        Args:
            guild: Discord guild-like object (must expose a `channels` iterable)

        Returns:
            List of discovered categories

        Raises:
            DiscordAPIError: If discovery fails
        """

        try:
            categories: list[DiscordCategory] = []

            for channel in getattr(guild, "channels", []):
                if isinstance(channel, GuildCategory):
                    category = DiscordCategory(
                        id=int(channel.id),
                        name=str(channel.name),
                        server_id=self.server_id,
                        position=int(getattr(channel, "position", 0) or 0),
                    )
                    await self.save_category(category)
                    categories.append(category)

            logger.info("Discovered %s categories", len(categories))
            return categories

        except Exception as e:
            raise DiscordAPIError("Failed to discover categories", cause=e) from e

    async def save_category(self, category: DiscordCategory) -> None:
        """Save category to database and JSONL.

        Args:
            category: Category to save
        """

        await self.db.save_category(category)
        await self.jsonl.write_category(category)
        logger.debug("Saved category: %s (ID: %s)", category.name, category.id)

    async def get_category_by_name(self, name: str) -> DiscordCategory:
        """Retrieve category by name.

        Args:
            name: Category name to search for

        Returns:
            Category matching name

        Raises:
            CategoryNotFoundError: If category not found
        """

        category = await self.db.get_category_by_name(name, self.server_id)
        if category is None:
            raise CategoryNotFoundError(f"Category '{name}' not found in server {self.server_id}")
        return category

    async def get_category(self, category_id: int) -> DiscordCategory:
        """Retrieve category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category object

        Raises:
            CategoryNotFoundError: If category not found
        """

        category = await self.db.get_category(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category {category_id} not found")
        return category
