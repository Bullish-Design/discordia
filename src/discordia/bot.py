# src/discordia/bot.py
from __future__ import annotations

"""Bot orchestrator.

The :class:`~discordia.bot.Bot` coordinates the Discord client, state discovery,
plugins, and handler routing.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Protocol

from discordia.config import BotConfig
from discordia.context import MessageContext
from discordia.discovery import DiscoveryEngine
from discordia.handlers import Handler
from discordia.plugins import Plugin
from discordia.registry import EntityRegistry
from discordia.state import Channel, MemoryState, Message, User

logger = logging.getLogger("discordia.bot")


class DiscordClient(Protocol):
    """Minimum client interface required by :class:`~discordia.bot.Bot`."""

    user: Any

    def add_listener(self, listener: Any) -> None: ...

    async def fetch_guild(self, guild_id: int) -> Any: ...

    def start(self) -> None: ...

    async def stop(self) -> None: ...


# Best-effort imports so the core package can be tested without interactions.
try:  # pragma: no cover
    from interactions import Client as _InteractionsClient
    from interactions import Intents as _Intents
    from interactions import listen as _listen
    from interactions.api.events import MessageCreate as _MessageCreate
    from interactions.api.events import Ready as _Ready

    Client = _InteractionsClient
    Intents = _Intents
    listen = _listen
    MessageCreate = _MessageCreate
    Ready = _Ready
except Exception:  # pragma: no cover

    class Intents(int):
        """Fallback intents placeholder."""

        DEFAULT = 0
        GUILD_MESSAGES = 0
        MESSAGE_CONTENT = 0

    def listen() -> Any:
        """Fallback decorator compatible with interactions.listen."""

        def decorator(func: Any) -> Any:
            return func

        return decorator

    class Client:  # noqa: D101
        def __init__(self, token: str, intents: int):
            self.token = token
            self.intents = intents
            self.user: Any = None

        def add_listener(self, listener: Any) -> None:
            return None

        async def fetch_guild(self, guild_id: int) -> Any:
            raise RuntimeError("Discord client unavailable")

        def start(self) -> None:
            raise RuntimeError("Discord client unavailable")

        async def stop(self) -> None:
            return None

    class Ready:  # noqa: D101
        user: Any

    class MessageCreate:  # noqa: D101
        message: Any


def _safe_username(value: Any) -> str:
    text = str(value or "")
    text = text.strip() or "unknown"
    # Username validation requires 2-32 characters.
    if len(text) == 1:
        text = f"{text}_"
    return text[:32]


def _safe_now() -> datetime:
    return datetime.now(UTC)


class Bot:
    """Main orchestrator for Discordia."""

    def __init__(
        self,
        config: BotConfig,
        handlers: list[Handler] | None = None,
        plugins: list[Plugin] | None = None,
        client: DiscordClient | None = None,
    ):
        self.config = config
        self.handlers = handlers or []
        self.plugins = plugins or []

        self.state = MemoryState()
        self.registry = EntityRegistry(self.state)
        self.discovery = DiscoveryEngine(self.state, config.server_id)

        self.client: DiscordClient
        if client is not None:
            self.client = client
        else:
            intents = Intents.DEFAULT | Intents.GUILD_MESSAGES | Intents.MESSAGE_CONTENT
            self.client = Client(token=config.discord_token.get_secret_value(), intents=intents)

        self._setup_listeners()

    def _setup_listeners(self) -> None:
        """Register Discord event listeners."""

        @listen()
        async def on_ready(event: Ready) -> None:
            await self._on_ready(event)

        @listen()
        async def on_message_create(event: MessageCreate) -> None:
            await self._on_message(event)

        self.client.add_listener(on_ready)
        self.client.add_listener(on_message_create)

    async def _on_ready(self, event: Any) -> None:
        """Handle the Discord ready event."""

        try:
            username = getattr(getattr(self.client, "user", None), "username", None)
            if not username:
                username = getattr(getattr(event, "user", None), "username", "<unknown>")
            logger.info("Bot ready as %s", username)

            guild = await self.client.fetch_guild(int(self.config.server_id))
            await self.discovery.discover_categories(guild)
            await self.discovery.discover_channels(guild)

            for plugin in self.plugins:
                try:
                    await plugin.on_ready(self, guild)
                except Exception as exc:
                    logger.exception("Plugin on_ready failed: %s", exc)

            logger.info("Bot operational")
        except Exception as exc:
            logger.exception("Error in on_ready: %s", exc)

    async def _ensure_channel(self, raw_channel: Any) -> Channel | None:
        channel_id = int(getattr(raw_channel, "id", 0) or 0)
        if channel_id <= 0:
            return None

        existing = await self.state.get_channel(channel_id)
        if existing is not None:
            return existing

        parent_id_raw = getattr(raw_channel, "parent_id", None)
        parent_id = int(parent_id_raw) if parent_id_raw else None
        if parent_id is not None and await self.state.get_category(parent_id) is None:
            parent_id = None

        topic_raw = getattr(raw_channel, "topic", None)
        topic: str | None = str(topic_raw) if topic_raw else None

        try:
            channel = Channel(
                id=channel_id,
                name=str(getattr(raw_channel, "name", "unknown")),
                server_id=self.config.server_id,
                category_id=parent_id,
                topic=topic,
            )
            await self.state.save_channel(channel)
            return channel
        except Exception as exc:
            logger.warning("Failed to save channel %s: %s", channel_id, exc)
            return None

    async def _on_message(self, event: Any) -> None:
        """Handle a Discord message create event."""

        try:
            message = getattr(event, "message", None)
            if message is None:
                return

            author = getattr(message, "author", None)
            if author is None:
                return

            if bool(getattr(author, "bot", False)):
                return

            channel = await self._ensure_channel(getattr(message, "channel", None))
            if channel is None:
                return

            user = User(
                id=int(getattr(author, "id", 0) or 0),
                username=_safe_username(getattr(author, "username", None)),
                bot=bool(getattr(author, "bot", False)),
            )
            await self.state.save_user(user)

            timestamp = getattr(message, "timestamp", None) or _safe_now()
            inbound = Message(
                id=int(getattr(message, "id", 0) or 0),
                content=str(getattr(message, "content", ""))[:2000],
                author_id=user.id,
                channel_id=channel.id,
                timestamp=timestamp,
            )
            await self.state.save_message(inbound)

            ctx = MessageContext(
                message_id=inbound.id,
                content=inbound.content,
                author=user,
                channel=channel,
                store=self.state,
                timestamp=inbound.timestamp,
            )

            for plugin in self.plugins:
                try:
                    await plugin.on_message(self, ctx)
                except Exception as exc:
                    logger.exception("Plugin on_message failed: %s", exc)

            for handler in self.handlers:
                if not await handler.can_handle(ctx):
                    continue

                response = await handler.handle(ctx)
                if response:
                    await self._reply_and_record(message, channel.id, response)
                break
        except Exception as exc:
            logger.exception("Error processing message: %s", exc)

    async def _reply_and_record(self, raw_message: Any, channel_id: int, response: str) -> None:
        reply_fn = getattr(raw_message, "reply", None)
        if not callable(reply_fn):
            return

        reply_result: Any = await reply_fn(response)

        bot_user_raw = getattr(self.client, "user", None)
        bot_id = int(getattr(bot_user_raw, "id", 0) or 0)
        if bot_id <= 0:
            return

        await self.state.save_user(
            User(
                id=bot_id,
                username=_safe_username(getattr(bot_user_raw, "username", "bot")),
                bot=True,
            )
        )

        reply_id = int(getattr(reply_result, "id", 0) or 0)
        if reply_id <= 0:
            reply_id = int(getattr(raw_message, "id", 0) or 0) + 1
            while reply_id in self.state.messages:
                reply_id += 1

        timestamp = getattr(reply_result, "timestamp", None) or _safe_now()
        try:
            await self.state.save_message(
                Message(
                    id=reply_id,
                    content=str(response)[:2000],
                    author_id=bot_id,
                    channel_id=channel_id,
                    timestamp=timestamp,
                )
            )
        except Exception as exc:
            logger.warning("Failed to save bot reply message: %s", exc)

    def run(self) -> None:
        """Start the bot."""

        logger.info("Starting bot")
        self.client.start()

    async def stop(self) -> None:
        """Stop the bot."""

        logger.info("Stopping bot")
        await self.client.stop()


__all__ = [
    "Bot",
    "DiscordClient",
]
