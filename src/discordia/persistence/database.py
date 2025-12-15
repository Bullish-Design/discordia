# src/discordia/persistence/database.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, col, select

from discordia.exceptions import DatabaseError
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser

logger = logging.getLogger("discordia.database")


class DatabaseWriter:
    """Async database writer for Discord entities.

    Handles SQLite persistence using SQLModel with async operations.
    """

    def __init__(self, database_url: str) -> None:
        """Initialize database writer.

        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite+aiosqlite:///discordia.db)
        """

        self.database_url = database_url

        engine_kwargs: dict[str, Any] = {"echo": False}

        # SQLite in-memory databases need a static pool to persist across sessions.
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        self.engine = create_async_engine(database_url, **engine_kwargs)

        self._configure_sqlite_engine(self.engine.sync_engine)

        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        self._initialized = False

    @staticmethod
    def _configure_sqlite_engine(engine: Engine) -> None:
        """Apply SQLite connection settings.

        Ensures foreign key constraints are enforced.
        """

        if engine.dialect.name != "sqlite":
            return

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    async def initialize(self) -> None:
        """Create all tables if they don't exist."""

        if self._initialized:
            return

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            self._initialized = True
            logger.info("Database initialized")
        except Exception as e:  # pragma: no cover
            raise DatabaseError("Failed to initialize database", cause=e) from e

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Get an async database session.

        Commits on success and rolls back on failure.
        """

        if not self._initialized:
            await self.initialize()

        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise DatabaseError("Database session failed", cause=e) from e

    async def save_category(self, category: DiscordCategory) -> None:
        """Save or update category in database."""

        try:
            async with self.get_session() as session:
                session.add(category)
        except DatabaseError:
            raise
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to save category {category.id}", cause=e) from e

    async def save_channel(self, channel: DiscordTextChannel) -> None:
        """Save or update text channel in database."""

        try:
            async with self.get_session() as session:
                session.add(channel)
        except DatabaseError:
            raise
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to save channel {channel.id}", cause=e) from e

    async def save_message(self, message: DiscordMessage) -> None:
        """Save message to database."""

        try:
            async with self.get_session() as session:
                session.add(message)
        except DatabaseError as e:
            # Re-wrap session errors with a message-specific context.
            raise DatabaseError(f"Failed to save message {message.id}", cause=e) from e
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to save message {message.id}", cause=e) from e

    async def save_user(self, user: DiscordUser) -> None:
        """Save or update user in database."""

        try:
            async with self.get_session() as session:
                session.add(user)
        except DatabaseError:
            raise
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to save user {user.id}", cause=e) from e

    async def get_category(self, category_id: int) -> DiscordCategory | None:
        """Retrieve category by ID."""

        try:
            async with self.get_session() as session:
                return await session.get(DiscordCategory, category_id)
        except DatabaseError as e:
            raise DatabaseError(f"Failed to retrieve category {category_id}", cause=e) from e
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to retrieve category {category_id}", cause=e) from e

    async def get_category_by_name(self, name: str, server_id: int) -> DiscordCategory | None:
        """Retrieve category by name within a server.

        Args:
            name: Category name
            server_id: Server ID to search in

        Returns:
            Category if found, None otherwise
        """

        try:
            async with self.get_session() as session:
                statement = select(DiscordCategory).where(
                    DiscordCategory.name == name,
                    DiscordCategory.server_id == server_id,
                )
                result = await session.execute(statement)
                return result.scalar_one_or_none()
        except DatabaseError as e:
            raise DatabaseError(f"Failed to retrieve category by name: {name}", cause=e) from e
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to retrieve category by name: {name}", cause=e) from e

    async def get_channel(self, channel_id: int) -> DiscordTextChannel | None:
        """Retrieve channel by ID."""

        try:
            async with self.get_session() as session:
                return await session.get(DiscordTextChannel, channel_id)
        except DatabaseError as e:
            raise DatabaseError(f"Failed to retrieve channel {channel_id}", cause=e) from e
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to retrieve channel {channel_id}", cause=e) from e

    async def get_messages(self, channel_id: int, limit: int = 20) -> list[DiscordMessage]:
        """Retrieve recent messages from a channel.

        Args:
            channel_id: Channel to retrieve from
            limit: Maximum number of messages (default 20)

        Returns:
            List of messages ordered by timestamp (oldest first)
        """

        try:
            async with self.get_session() as session:
                statement = (
                    select(DiscordMessage)
                    .where(DiscordMessage.channel_id == channel_id)
                    .order_by(col(DiscordMessage.timestamp).desc(), col(DiscordMessage.id).desc())
                    .limit(limit)
                )
                result = await session.execute(statement)
                messages = list(result.scalars().all())
                return list(reversed(messages))
        except DatabaseError as e:
            raise DatabaseError(f"Failed to retrieve messages from channel {channel_id}", cause=e) from e
        except Exception as e:  # pragma: no cover
            raise DatabaseError(f"Failed to retrieve messages from channel {channel_id}", cause=e) from e

    async def close(self) -> None:
        """Close database connection."""

        await self.engine.dispose()
