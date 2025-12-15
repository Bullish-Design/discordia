# src/discordia/managers/channel_manager.py
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from discordia.exceptions import ChannelNotFoundError, DatabaseError, DiscordAPIError, JSONLError
from discordia.models.channel import DiscordTextChannel

if TYPE_CHECKING:
    from discordia.persistence.database import DatabaseWriter
    from discordia.persistence.jsonl import JSONLWriter

logger = logging.getLogger("discordia.channel_manager")


try:  # pragma: no cover
    from interactions.models.discord.channel import GuildText as GuildText
except Exception:  # pragma: no cover
    # Allows unit tests to run without importing interactions internals.
    class GuildText:  # type: ignore[no-redef]
        """Fallback GuildText type for runtime imports."""


class ChannelManager:
    """Manages Discord text channel operations."""

    LOG_CHANNEL_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def __init__(self, db: DatabaseWriter, jsonl: JSONLWriter, server_id: int) -> None:
        """Initialize channel manager.

        Args:
            db: Database writer
            jsonl: JSONL writer
            server_id: Discord server ID
        """

        self.db = db
        self.jsonl = jsonl
        self.server_id = server_id

    async def discover_channels(self, guild: Any) -> list[DiscordTextChannel]:
        """Discover all text channels in a guild.

        Args:
            guild: Discord guild-like object (must expose a `channels` iterable)

        Returns:
            List of discovered text channels

        Raises:
            DiscordAPIError: If discovery fails
        """

        try:
            channels: list[DiscordTextChannel] = []

            for channel in getattr(guild, "channels", []):
                if isinstance(channel, GuildText):
                    parent_id = getattr(channel, "parent_id", None)
                    text_channel = DiscordTextChannel(
                        id=int(channel.id),
                        name=str(channel.name),
                        category_id=int(parent_id) if parent_id else None,
                        server_id=self.server_id,
                        position=int(getattr(channel, "position", 0) or 0),
                    )
                    await self.save_channel(text_channel)
                    channels.append(text_channel)

            logger.info("Discovered %s text channels", len(channels))
            return channels

        except Exception as e:
            logger.error("Failed to discover channels: %s", e, exc_info=True)
            raise DiscordAPIError("Failed to discover channels", cause=e) from e

    async def save_channel(self, channel: DiscordTextChannel) -> None:
        """Save channel to database and JSONL.

        Args:
            channel: Channel to save
        """

        try:
            await self.db.save_channel(channel)
        except DatabaseError as e:
            logger.error(
                "Failed to persist channel %s to database: %s",
                channel.id,
                e,
                exc_info=True,
            )

        try:
            await self.jsonl.write_channel(channel)
        except JSONLError as e:
            logger.error(
                "Failed to persist channel %s to JSONL: %s",
                channel.id,
                e,
                exc_info=True,
            )
        logger.debug("Saved channel: %s (ID: %s)", channel.name, channel.id)

    async def get_channel(self, channel_id: int) -> DiscordTextChannel:
        """Retrieve channel by ID.

        Args:
            channel_id: Channel ID

        Returns:
            Channel object

        Raises:
            ChannelNotFoundError: If not found
        """

        try:
            channel = await self.db.get_channel(channel_id)
        except Exception as e:
            logger.error("Failed to get channel %s: %s", channel_id, e, exc_info=True)
            raise DiscordAPIError("Failed to get channel", cause=e) from e
        if channel is None:
            raise ChannelNotFoundError(f"Channel {channel_id} not found")
        return channel

    async def create_channel(self, guild: Any, name: str, category_id: int | None = None) -> DiscordTextChannel:
        """Create a new text channel.

        Args:
            guild: Discord guild-like object (must expose `create_text_channel`)
            name: Channel name
            category_id: Optional category ID

        Returns:
            Created channel

        Raises:
            DiscordAPIError: If creation fails
        """

        try:
            discord_channel = await guild.create_text_channel(name=name, parent_id=category_id)
            channel = DiscordTextChannel(
                id=int(discord_channel.id),
                name=str(discord_channel.name),
                category_id=category_id,
                server_id=self.server_id,
                position=int(getattr(discord_channel, "position", 0) or 0),
            )
            await self.save_channel(channel)
            logger.info("Created channel: %s (ID: %s)", name, channel.id)
            return channel
        except Exception as e:
            logger.error("Failed to create channel '%s': %s", name, e, exc_info=True)
            raise DiscordAPIError(f"Failed to create channel: {name}", cause=e) from e

    def is_log_channel(self, channel_name: str) -> bool:
        """Return True if channel name matches YYYY-MM-DD log channel format."""

        return bool(self.LOG_CHANNEL_PATTERN.match(channel_name))

    def get_daily_channel_name(self) -> str:
        """Get today's log channel name in YYYY-MM-DD format."""

        return datetime.utcnow().strftime("%Y-%m-%d")

    async def ensure_daily_log_channel(self, guild: Any, log_category_id: int) -> DiscordTextChannel:
        """Ensure today's log channel exists, creating it if missing.

        Args:
            guild: Discord guild-like object
            log_category_id: Category ID for log channels

        Returns:
            Today's log channel

        Raises:
            DiscordAPIError: If operations fail
        """

        channel_name = self.get_daily_channel_name()
        try:
            channel = await self.db.get_channel_by_name(channel_name, self.server_id)
        except Exception as e:
            logger.error("Failed to lookup daily log channel '%s': %s", channel_name, e, exc_info=True)
            channel = None
        if channel is not None:
            logger.debug("Daily log channel exists: %s", channel_name)
            return channel

        logger.warning("Daily log channel missing, creating: %s", channel_name)
        return await self.create_channel(guild=guild, name=channel_name, category_id=log_category_id)
