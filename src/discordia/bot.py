# src/discordia/bot.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from interactions import Client, Intents, listen
from interactions.api.events import MessageCreate, Ready

from discordia.managers.category_manager import CategoryManager
from discordia.persistence.database import DatabaseWriter
from discordia.persistence.jsonl import JSONLWriter
from discordia.settings import Settings

if TYPE_CHECKING:
    from interactions import Message

logger = logging.getLogger("discordia.bot")


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for Discordia.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class Bot:
    """Discordia Discord bot.

    Main bot class that composes managers and handles Discord events.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize bot with settings.

        Args:
            settings: Configuration settings
        """

        self.settings = settings

        # Initialize persistence
        self.db = DatabaseWriter(settings.database_url)
        self.jsonl = JSONLWriter(settings.jsonl_path)

        # Initialize managers
        self.category_manager = CategoryManager(
            db=self.db,
            jsonl=self.jsonl,
            server_id=settings.server_id,
        )

        # Create Discord client
        self.client = Client(
            token=settings.discord_token,
            intents=Intents.DEFAULT | Intents.GUILD_MESSAGES | Intents.MESSAGE_CONTENT,
        )

        # Register event listeners
        self._setup_listeners()

        logger.info("Bot initialized")

    def _setup_listeners(self) -> None:
        """Register event listeners with Discord client."""

        @listen()
        async def on_ready(event: Ready) -> None:
            """Handle bot ready event."""

            await self._on_ready(event)

        @listen()
        async def on_message_create(event: MessageCreate) -> None:
            """Handle new message events."""

            await self._on_message(event)

        self.client.add_listener(on_ready)
        self.client.add_listener(on_message_create)

    async def _on_ready(self, event: Ready) -> None:
        """Process ready event.

        Args:
            event: Ready event from Discord
        """

        logger.info("Bot ready as %s", event.user.username)
        logger.info("Connected to %s guilds", len(event.guilds))

        await self.db.initialize()
        logger.info("Database initialized")

        guild = await self.client.fetch_guild(self.settings.server_id)
        await self.category_manager.discover_categories(guild)

    async def _on_message(self, event: MessageCreate) -> None:
        """Process new message event.

        Args:
            event: MessageCreate event from Discord
        """

        message: Message = event.message

        # Ignore bot's own messages
        if message.author.bot:
            return

        logger.debug(
            "Message received: %s from %s in channel %s",
            message.id,
            message.author.username,
            message.channel.id,
        )

        # TODO: Message handling will be implemented in later steps

    def run(self) -> None:
        """Start the bot.

        Blocks until bot is stopped.
        """

        logger.info("Starting bot...")
        self.client.start()

    async def stop(self) -> None:
        """Stop the bot gracefully."""

        logger.info("Stopping bot...")
        await self.db.close()
        await self.client.stop()
