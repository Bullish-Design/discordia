# src/discordia/managers/message_handler.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from discordia.exceptions import DatabaseError, JSONLError, LLMAPIError, MessageSendError
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser

if TYPE_CHECKING:
    from discordia.llm.client import LLMClient
    from discordia.managers.channel_manager import ChannelManager
    from discordia.persistence.database import DatabaseWriter
    from discordia.persistence.jsonl import JSONLWriter

logger = logging.getLogger("discordia.message_handler")


class MessageHandler:
    """Handles Discord message processing and LLM interactions."""

    def __init__(
        self,
        db: DatabaseWriter,
        jsonl: JSONLWriter,
        llm_client: LLMClient,
        channel_manager: ChannelManager,
        context_limit: int = 20,
        max_message_length: int = 2000,
    ) -> None:
        """Initialize message handler.

        Args:
            db: Database writer.
            jsonl: JSONL writer.
            llm_client: LLM client.
            channel_manager: Channel manager.
            context_limit: Number of messages to load for context.
            max_message_length: Discord message length limit.
        """

        self.db = db
        self.jsonl = jsonl
        self.llm_client = llm_client
        self.channel_manager = channel_manager
        self.context_limit = context_limit
        self.max_message_length = max_message_length

    async def save_user(self, discord_user: Any) -> DiscordUser:
        """Save a Discord user to persistence.

        Args:
            discord_user: A Discord user-like object.

        Returns:
            Persisted DiscordUser model.
        """

        user = DiscordUser(
            id=int(getattr(discord_user, "id")),
            username=str(getattr(discord_user, "username")),
            bot=bool(getattr(discord_user, "bot", False) or False),
        )

        try:
            await self.db.save_user(user)
            await self.jsonl.write_user(user)
        except (DatabaseError, JSONLError) as e:
            logger.error("Failed to save user %s: %s", user.id, e)

        return user

    async def save_message(self, discord_message: Any) -> DiscordMessage:
        """Save a Discord message to persistence.

        Args:
            discord_message: A Discord message-like object.

        Returns:
            Persisted DiscordMessage model.
        """

        timestamp = getattr(discord_message, "timestamp", None) or datetime.utcnow()
        edited_at = getattr(discord_message, "edited_timestamp", None)

        message = DiscordMessage(
            id=int(getattr(discord_message, "id")),
            content=str(getattr(discord_message, "content", "") or ""),
            author_id=int(getattr(getattr(discord_message, "author"), "id")),
            channel_id=int(getattr(getattr(discord_message, "channel"), "id")),
            timestamp=timestamp,
            edited_at=edited_at,
        )

        try:
            await self.db.save_message(message)
            await self.jsonl.write_message(message)
        except (DatabaseError, JSONLError) as e:
            logger.error("Failed to save message %s: %s", message.id, e)

        return message

    async def get_context_messages(self, channel_id: int) -> list[DiscordMessage]:
        """Load recent messages from a channel for LLM context."""

        try:
            messages = await self.db.get_messages(channel_id=channel_id, limit=self.context_limit)
            logger.debug("Loaded %s messages for context", len(messages))
            return messages
        except DatabaseError as e:
            logger.error("Failed to load context for channel %s: %s", channel_id, e)
            return []

    def split_message(self, text: str) -> list[str]:
        """Split long text into chunks under the Discord limit."""

        if len(text) <= self.max_message_length:
            return [text]

        chunks: list[str] = []
        current = ""

        for line in text.split("\n"):
            delimiter = "\n" if current else ""
            if len(current) + len(delimiter) + len(line) > self.max_message_length:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = f"{current}{delimiter}{line}"

        if current:
            chunks.append(current)

        return chunks

    async def handle_message(self, discord_message: Any) -> None:
        """Process an incoming Discord message.

        Workflow:
        1. Ignore bot messages.
        2. Persist user and message.
        3. Check if message is in a daily log channel.
        4. Load recent context.
        5. Call LLM and reply.
        6. Persist bot replies.

        Args:
            discord_message: A Discord message-like object.
        """

        if bool(getattr(getattr(discord_message, "author", None), "bot", False)):
            return

        try:
            await self.save_user(getattr(discord_message, "author"))
            message = await self.save_message(discord_message)

            channel_obj = await getattr(getattr(discord_message, "channel"), "fetch")()
            channel_name = str(getattr(channel_obj, "name", ""))

            if not self.channel_manager.is_log_channel(channel_name):
                logger.debug("Ignoring message in non-log channel: %s", channel_name)
                return

            logger.info("Processing message in log channel: %s", channel_name)

            context = await self.get_context_messages(message.channel_id)
            if not context:
                logger.warning("No context available, skipping LLM call")
                return

            try:
                response_text = await self.llm_client.generate_response(context)
            except LLMAPIError as e:
                error_msg = f"⚠️ LLM Error: {e.message}"
                await getattr(discord_message, "reply")(error_msg)
                logger.error("LLM failed for message %s: %s", message.id, e)
                return

            chunks = self.split_message(response_text)

            for chunk in chunks:
                try:
                    sent_message = await getattr(discord_message, "reply")(chunk)

                    bot_timestamp = getattr(sent_message, "timestamp", None) or datetime.utcnow()
                    bot_message = DiscordMessage(
                        id=int(getattr(sent_message, "id")),
                        content=str(chunk),
                        author_id=int(getattr(getattr(sent_message, "author"), "id")),
                        channel_id=message.channel_id,
                        timestamp=bot_timestamp,
                        edited_at=getattr(sent_message, "edited_timestamp", None),
                    )

                    await self.db.save_message(bot_message)
                    await self.jsonl.write_message(bot_message)

                except Exception as e:
                    logger.error("Failed to send message chunk: %s", e)
                    raise MessageSendError("Failed to send response to Discord", cause=e) from e

        except Exception as e:
            logger.error("Error handling message %s: %s", getattr(discord_message, "id", "unknown"), e, exc_info=True)
            return
