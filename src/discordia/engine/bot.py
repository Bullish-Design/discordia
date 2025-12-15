# src/discordia/engine/bot.py
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from discordia.engine.context import MessageContext
from discordia.settings import Settings
from discordia.state.memory import MemoryState
from discordia.state.models import Message, User
from discordia.state.registry import EntityRegistry

if TYPE_CHECKING:
    from discordia.handlers.protocol import MessageHandler
    from discordia.templates.server import ServerTemplate

logger = logging.getLogger("discordia.engine.bot")


try:
    from interactions import Client, Intents, listen
    from interactions.api.events import MessageCreate, Ready
except Exception:

    class Intents(int):
        DEFAULT = 0
        GUILD_MESSAGES = 0
        MESSAGE_CONTENT = 0

    def listen():
        def decorator(func):
            return func

        return decorator

    class Client:
        def __init__(self, token: str, intents: int) -> None:
            self.token = token
            self.intents = intents

        def add_listener(self, _listener: Any) -> None:
            return

        async def fetch_guild(self, _guild_id: int) -> Any:
            raise RuntimeError("Discord client unavailable")

        async def stop(self) -> None:
            return

        def start(self) -> None:
            raise RuntimeError("Discord client unavailable")

    class Ready:
        user: Any
        guilds: list[Any]

    class MessageCreate:
        message: Any


class Bot:
    """Thin event dispatcher that delegates to handlers."""

    def __init__(
        self, settings: Settings, template: ServerTemplate | None = None, handlers: list[MessageHandler] | None = None
    ) -> None:
        self.settings = settings
        self.template = template
        self.handlers = handlers or []

        self.state = MemoryState()
        self.registry = EntityRegistry(self.state)

        from discordia.engine.discovery import DiscoveryEngine
        from discordia.engine.reconciler import Reconciler

        self.discovery = DiscoveryEngine(self.state, settings.server_id)
        self.reconciler = Reconciler(self.state, self.registry, settings.server_id)

        self.client = Client(
            token=settings.discord_token.get_secret_value(),
            intents=Intents.DEFAULT | Intents.GUILD_MESSAGES | Intents.MESSAGE_CONTENT,
        )

        self._setup_listeners()
        self._reconcile_task: asyncio.Task[None] | None = None

    def _setup_listeners(self) -> None:
        """Register event listeners."""

        @listen()
        async def on_ready(event: Ready) -> None:
            await self._on_ready(event)

        @listen()
        async def on_message_create(event: MessageCreate) -> None:
            await self._on_message(event)

        self.client.add_listener(on_ready)
        self.client.add_listener(on_message_create)

    async def _on_ready(self, event: Ready) -> None:
        """Process ready event."""
        try:
            logger.info("Bot ready as %s", event.user.username)

            guild = await self.client.fetch_guild(self.settings.server_id)
            await self.discovery.discover_categories(guild)
            await self.discovery.discover_channels(guild)

            if self.template and self.settings.auto_reconcile:
                await self.reconciler.reconcile(guild, self.template)

            if self.settings.reconcile_interval > 0:
                self._reconcile_task = asyncio.create_task(self._reconcile_loop())

            logger.info("Bot ready and operational")
        except Exception as e:
            logger.error("Error in on_ready: %s", e, exc_info=True)

    async def _reconcile_loop(self) -> None:
        """Periodic reconciliation loop."""
        while True:
            await asyncio.sleep(self.settings.reconcile_interval)
            if self.template:
                try:
                    guild = await self.client.fetch_guild(self.settings.server_id)
                    await self.reconciler.reconcile(guild, self.template)
                except Exception as e:
                    logger.error("Reconciliation loop error: %s", e)

    async def _on_message(self, event: MessageCreate) -> None:
        """Process message event."""
        try:
            message = event.message
            if message.author.bot:
                return

            user = User(
                id=int(message.author.id),
                username=str(message.author.username)[:32],
                bot=bool(message.author.bot),
            )
            await self.state.save_user(user)

            msg = Message(
                id=int(message.id),
                content=str(message.content)[:2000],
                author_id=user.id,
                channel_id=int(message.channel.id),
                timestamp=message.timestamp,
            )
            await self.state.save_message(msg)

            channel = await self.state.get_channel(msg.channel_id)
            if not channel:
                return

            ctx = MessageContext(
                message_id=msg.id,
                content=msg.content,
                author_id=user.id,
                author_name=user.username,
                channel_id=channel.id,
                channel_name=channel.name,
                channel=channel,
                author=user,
                store=self.state,
            )

            for handler in self.handlers:
                if await handler.can_handle(ctx):
                    response = await handler.handle(ctx)
                    if response:
                        await message.reply(response)
                        bot_msg = Message(
                            id=int(message.id) + 1,
                            content=response[:2000],
                            author_id=int(self.client.user.id),
                            channel_id=channel.id,
                            timestamp=msg.timestamp,
                        )
                        try:
                            await self.state.save_message(bot_msg)
                        except Exception as e:
                            logger.warning("Failed to save bot message: %s", e)
                    break

        except Exception as e:
            logger.error("Error processing message: %s", e, exc_info=True)

    def run(self) -> None:
        """Start the bot."""
        logger.info("Starting bot...")
        self.client.start()

    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping bot...")
        if self._reconcile_task:
            self._reconcile_task.cancel()
        await self.client.stop()


__all__ = ["Bot"]
