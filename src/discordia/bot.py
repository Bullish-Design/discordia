# src/discordia/bot.py
from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

try:  # pragma: no cover
    from interactions import Client, Intents, listen
    from interactions.api.events import MessageCreate, Ready
except Exception:  # pragma: no cover
    # The core library can be imported without optional Discord dependencies.
    from typing import Any, Callable, Coroutine

    class Intents(int):
        """Fallback bitfield for Discord intents."""

        DEFAULT = 0
        GUILD_MESSAGES = 0
        MESSAGE_CONTENT = 0

    def listen() -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
        """Fallback no-op decorator for event listeners."""

        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
            return func

        return decorator

    class Client:  # type: ignore[no-redef]
        """Fallback Discord client.

        This is intentionally minimal: unit tests patch this type and the
        production runtime should use the interactions.py package.
        """

        def __init__(self, token: str, intents: int) -> None:
            self.token = token
            self.intents = intents

        def add_listener(self, _listener: Any) -> None:
            return

        async def fetch_guild(self, _guild_id: int) -> Any:
            raise RuntimeError("Discord client is unavailable (interactions.py not installed)")

        async def stop(self) -> None:
            return

        def start(self) -> None:
            raise RuntimeError("Discord client is unavailable (interactions.py not installed)")

    class Ready:  # type: ignore[no-redef]
        """Fallback ready event."""

        user: Any
        guilds: list[Any]

    class MessageCreate:  # type: ignore[no-redef]
        """Fallback message create event."""

        message: Any

from discordia.exceptions import CategoryNotFoundError
from discordia.llm.client import LLMClient
from discordia.managers.category_manager import CategoryManager
from discordia.managers.channel_manager import ChannelManager
from discordia.managers.message_handler import MessageHandler
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

        # Initialize LLM client
        self.llm_client = LLMClient(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )

        # Initialize managers
        self.category_manager = CategoryManager(
            db=self.db,
            jsonl=self.jsonl,
            server_id=settings.server_id,
        )

        self.channel_manager = ChannelManager(
            db=self.db,
            jsonl=self.jsonl,
            server_id=settings.server_id,
        )

        self.message_handler = MessageHandler(
            db=self.db,
            jsonl=self.jsonl,
            llm_client=self.llm_client,
            channel_manager=self.channel_manager,
            context_limit=settings.message_context_limit,
            max_message_length=settings.max_message_length,
        )

        # Create Discord client
        self.client = Client(
            token=settings.discord_token,
            intents=Intents.DEFAULT | Intents.GUILD_MESSAGES | Intents.MESSAGE_CONTENT,
        )

        # Register event listeners
        self._setup_listeners()

        # Track last date for daily channel checks
        self._last_date_checked: date | None = None

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

    async def _ensure_daily_log_channel(self) -> None:
        """Ensure today's log channel exists.

        Called on startup and when date changes.
        Creates channel in log category if missing.
        """

        today = date.today()

        # Skip if already checked today
        if self._last_date_checked == today:
            return

        try:
            log_category = await self.category_manager.get_category_by_name(self.settings.log_category_name)
            guild = await self.client.fetch_guild(self.settings.server_id)
            channel = await self.channel_manager.ensure_daily_log_channel(guild, log_category.id)

            logger.info("Daily log channel ready: %s", channel.name)
            self._last_date_checked = today

        except CategoryNotFoundError:
            logger.error(
                "Log category '%s' not found. Please create it manually in Discord.",
                self.settings.log_category_name,
            )
        except Exception as e:
            logger.error("Failed to ensure daily log channel: %s", e)

    async def _on_ready(self, event: Ready) -> None:
        """Process ready event.

        Args:
            event: Ready event from Discord
        """

        try:
            logger.info("Bot ready as %s", event.user.username)
            logger.info("Connected to %s guilds", len(event.guilds))

            try:
                await self.db.initialize()
                logger.info("Database initialized")
            except Exception as e:
                logger.error("Database initialization failed: %s", e, exc_info=True)

            try:
                guild = await self.client.fetch_guild(self.settings.server_id)
            except Exception as e:
                logger.error("Failed to fetch guild %s: %s", self.settings.server_id, e, exc_info=True)
                return

            try:
                await self.category_manager.discover_categories(guild)
            except Exception as e:
                logger.error("Category discovery failed: %s", e, exc_info=True)

            try:
                await self.channel_manager.discover_channels(guild)
            except Exception as e:
                logger.error("Channel discovery failed: %s", e, exc_info=True)

            if self.settings.auto_create_daily_logs:
                await self._ensure_daily_log_channel()

            logger.info("Bot ready and operational")
        except Exception as e:
            logger.error("Unhandled error in on_ready: %s", e, exc_info=True)

    async def _on_message(self, event: MessageCreate) -> None:
        """Process new message event.

        Args:
            event: MessageCreate event from Discord
        """

        try:
            message: Message = event.message

            # Ignore bot's own messages
            if message.author.bot:
                return

            # Check for daily channel before processing first message of each day
            if self.settings.auto_create_daily_logs:
                try:
                    await self._ensure_daily_log_channel()
                except Exception as e:
                    logger.error("Daily log channel check failed: %s", e, exc_info=True)

            logger.debug(
                "Message received: %s from %s in channel %s",
                message.id,
                message.author.username,
                message.channel.id,
            )

            try:
                await self.message_handler.handle_message(message)
            except Exception as e:
                # MessageHandler should be resilient, but never let exceptions escape to the gateway.
                logger.error("Unhandled error processing message %s: %s", message.id, e, exc_info=True)
        except Exception as e:
            logger.error("Unhandled error in on_message handler: %s", e, exc_info=True)

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
