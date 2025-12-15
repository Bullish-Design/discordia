# src/discordia/managers/message_handler.py
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from discordia.exceptions import ContextTooLargeError, DatabaseError, JSONLError, LLMAPIError
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

        user_id = int(getattr(discord_user, "id", 0) or 0)
        if user_id <= 0:
            user_id = 1

        username = str(getattr(discord_user, "username", "") or "").strip() or "unknown"
        if len(username) > 32:
            username = username[:32]

        try:
            user = DiscordUser(
                id=user_id,
                username=username,
                bot=bool(getattr(discord_user, "bot", False) or False),
            )
        except Exception as e:
            logger.error("Failed to build DiscordUser model (id=%s): %s", user_id, e, exc_info=True)
            user = DiscordUser(id=1, username="unknown", bot=False)

        try:
            await self.db.save_user(user)
        except DatabaseError as e:
            logger.error("Failed to persist user %s to database: %s", user.id, e, exc_info=True)

        try:
            await self.jsonl.write_user(user)
        except JSONLError as e:
            logger.error("Failed to persist user %s to JSONL: %s", user.id, e, exc_info=True)

        return user

    async def save_message(self, discord_message: Any) -> DiscordMessage:
        """Save a Discord message to persistence.

        Args:
            discord_message: A Discord message-like object.

        Returns:
            Persisted DiscordMessage model.
        """

        message_id = int(getattr(discord_message, "id", 0) or 0)
        if message_id <= 0:
            message_id = 1

        content = str(getattr(discord_message, "content", "") or "")
        if len(content) > self.max_message_length:
            content = content[: self.max_message_length]

        author = getattr(discord_message, "author", None)
        channel = getattr(discord_message, "channel", None)
        author_id = int(getattr(author, "id", 0) or 0)
        channel_id = int(getattr(channel, "id", 0) or 0)
        if author_id <= 0:
            author_id = 1
        if channel_id <= 0:
            channel_id = 1

        timestamp = getattr(discord_message, "timestamp", None)
        if not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()

        edited_at = getattr(discord_message, "edited_timestamp", None)
        if edited_at is not None and not isinstance(edited_at, datetime):
            edited_at = None

        message = DiscordMessage(
            id=message_id,
            content=content,
            author_id=author_id,
            channel_id=channel_id,
            timestamp=timestamp,
            edited_at=edited_at,
        )

        try:
            await self.db.save_message(message)
        except DatabaseError as e:
            logger.error("Failed to persist message %s to database: %s", message.id, e, exc_info=True)

        try:
            await self.jsonl.write_message(message)
        except JSONLError as e:
            logger.error("Failed to persist message %s to JSONL: %s", message.id, e, exc_info=True)

        return message

    async def get_context_messages(self, channel_id: int) -> list[DiscordMessage]:
        """Load recent messages from a channel for LLM context."""

        try:
            messages = await self.db.get_messages(channel_id=channel_id, limit=self.context_limit)
            logger.debug("Loaded %s messages for context", len(messages))
            return messages
        except DatabaseError as e:
            logger.error("Failed to load context for channel %s: %s", channel_id, e, exc_info=True)
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

        message_id = int(getattr(discord_message, "id", 0) or 0)

        try:
            # Save user (non-fatal if fails)
            try:
                await self.save_user(getattr(discord_message, "author"))
            except Exception as e:
                logger.error("Failed to save user for message %s: %s", message_id, e, exc_info=True)

            # Save message (non-fatal if fails)
            try:
                message = await self.save_message(discord_message)
            except Exception as e:
                logger.error("Failed to save message %s: %s", message_id, e, exc_info=True)
                safe_content = str(getattr(discord_message, "content", "") or "")[: self.max_message_length]
                timestamp = getattr(discord_message, "timestamp", None) or datetime.utcnow()
                author = getattr(discord_message, "author", None)
                channel = getattr(discord_message, "channel", None)
                message = DiscordMessage(
                    id=message_id if message_id > 0 else 1,
                    content=safe_content,
                    author_id=int(getattr(author, "id", 1) or 1),
                    channel_id=int(getattr(channel, "id", 1) or 1),
                    timestamp=timestamp,
                )

            # Check if in log channel
            try:
                channel_obj = await getattr(getattr(discord_message, "channel"), "fetch")()
            except Exception as e:
                logger.error("Failed to fetch channel for message %s: %s", message_id, e, exc_info=True)
                return

            channel_name = str(getattr(channel_obj, "name", ""))
            if not self.channel_manager.is_log_channel(channel_name):
                logger.debug("Ignoring message %s in non-log channel: %s", message_id, channel_name)
                return

            logger.info("Processing message %s in log channel: %s", message_id, channel_name)

            # Load context
            try:
                context = await self.get_context_messages(message.channel_id)
            except Exception as e:
                logger.error("Failed to load context for message %s: %s", message_id, e, exc_info=True)
                try:
                    await getattr(discord_message, "reply")(
                        "⚠️ Error: Could not load conversation history."
                    )
                except Exception:
                    pass
                return

            if not context:
                logger.warning("No context available for message %s", message_id)
                try:
                    await getattr(discord_message, "reply")(
                        "⚠️ No conversation history available yet."
                    )
                except Exception:
                    pass
                return

            # Generate LLM response
            try:
                response_text = await self.llm_client.generate_response(context)
            except ContextTooLargeError as e:
                error_msg = (
                    "⚠️ Conversation history is too long. "
                    "Try starting a new topic in a fresh channel."
                )
                try:
                    await getattr(discord_message, "reply")(error_msg)
                except Exception:
                    pass
                logger.warning("Context too large for message %s: %s", message_id, e)
                return
            except LLMAPIError as e:
                error_msg = "⚠️ Unable to generate response. Please try again."
                try:
                    await getattr(discord_message, "reply")(error_msg)
                except Exception:
                    pass
                logger.error("LLM failed for message %s: %s", message_id, e, exc_info=True)
                return

            chunks = self.split_message(response_text)
            for i, chunk in enumerate(chunks, start=1):
                sent_message: Any | None = None
                try:
                    sent_message = await getattr(discord_message, "reply")(chunk)
                    logger.debug("Sent response chunk %s/%s for message %s", i, len(chunks), message_id)
                except Exception as e:
                    logger.warning(
                        "Failed to send response chunk %s/%s for message %s: %s",
                        i,
                        len(chunks),
                        message_id,
                        e,
                    )
                    try:
                        await asyncio.sleep(1)
                        sent_message = await getattr(discord_message, "reply")(chunk)
                        logger.info("Retry succeeded for chunk %s/%s (message %s)", i, len(chunks), message_id)
                    except Exception as e2:
                        logger.error(
                            "Failed to send chunk %s/%s after retry for message %s: %s",
                            i,
                            len(chunks),
                            message_id,
                            e2,
                            exc_info=True,
                        )
                        try:
                            await getattr(discord_message, "reply")(
                                "⚠️ Error: Unable to send complete response."
                            )
                        except Exception:
                            pass
                        break

                if sent_message is None:
                    break

                # Save bot message (non-fatal if fails)
                try:
                    bot_timestamp = getattr(sent_message, "timestamp", None)
                    if not isinstance(bot_timestamp, datetime):
                        bot_timestamp = datetime.utcnow()

                    raw_edited = getattr(sent_message, "edited_timestamp", None)
                    edited_at = raw_edited if isinstance(raw_edited, datetime) else None
                    bot_author = getattr(sent_message, "author", None)
                    bot_message = DiscordMessage(
                        id=int(getattr(sent_message, "id", 0) or 0) or 1,
                        content=str(chunk)[: self.max_message_length],
                        author_id=int(getattr(bot_author, "id", 1) or 1),
                        channel_id=message.channel_id,
                        timestamp=bot_timestamp,
                        edited_at=edited_at,
                    )
                    try:
                        await self.db.save_message(bot_message)
                    except DatabaseError as e:
                        logger.error(
                            "Failed to persist bot message %s to database: %s",
                            bot_message.id,
                            e,
                            exc_info=True,
                        )
                    try:
                        await self.jsonl.write_message(bot_message)
                    except JSONLError as e:
                        logger.error(
                            "Failed to persist bot message %s to JSONL: %s",
                            bot_message.id,
                            e,
                            exc_info=True,
                        )
                except Exception as e:
                    logger.error("Failed to create/persist bot message for %s: %s", message_id, e, exc_info=True)

        except Exception as e:
            logger.error("Unexpected error handling message %s: %s", message_id, e, exc_info=True)
            try:
                await getattr(discord_message, "reply")(
                    "⚠️ An unexpected error occurred. Please try again."
                )
            except Exception:
                pass
            return
