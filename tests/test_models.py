# tests/test_models.py
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser


def _create_sqlite_engine() -> Engine:
    """Create an in-memory SQLite engine with foreign keys enabled."""

    engine = create_engine("sqlite:///:memory:")

    # Ensure foreign key enforcement is enabled for SQLite.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


class TestDiscordCategory:
    """Tests for DiscordCategory model."""

    def test_create_category_with_required_fields(self) -> None:
        """Category can be created with just required fields."""
        category = DiscordCategory(
            id=123456789,
            name="General",
            server_id=987654321,
        )
        assert category.id == 123456789
        assert category.name == "General"
        assert category.server_id == 987654321
        assert category.position == 0
        assert isinstance(category.created_at, datetime)

    def test_category_to_discord_format(self) -> None:
        """Category converts to Discord API format."""
        category = DiscordCategory(
            id=123,
            name="Test",
            server_id=456,
            position=5,
        )
        result = category.to_discord_format()
        assert result["id"] == 123
        assert result["name"] == "Test"
        assert result["guild_id"] == 456
        assert result["position"] == 5

    def test_category_name_too_long(self) -> None:
        """Category name cannot exceed 100 characters."""
        with pytest.raises(ValidationError):
            DiscordCategory(
                id=123,
                name="a" * 101,
                server_id=456,
            )


class TestDiscordTextChannel:
    """Tests for DiscordTextChannel model."""

    def test_create_channel_with_required_fields(self) -> None:
        """Channel can be created with required fields."""
        channel = DiscordTextChannel(
            id=111,
            name="general",
            server_id=222,
        )
        assert channel.id == 111
        assert channel.name == "general"
        assert channel.category_id is None
        assert channel.server_id == 222
        assert channel.position == 0
        assert isinstance(channel.created_at, datetime)

    def test_channel_with_category(self) -> None:
        """Channel can belong to a category."""
        channel = DiscordTextChannel(
            id=111,
            name="announcements",
            category_id=333,
            server_id=222,
        )
        assert channel.category_id == 333

    def test_channel_name_validation(self) -> None:
        """Channel name must be lowercase with hyphens."""
        channel = DiscordTextChannel(id=1, name="valid-channel", server_id=2)
        assert channel.name == "valid-channel"

        with pytest.raises(ValidationError):
            DiscordTextChannel(id=1, name="Invalid", server_id=2)

        with pytest.raises(ValidationError):
            DiscordTextChannel(id=1, name="invalid channel", server_id=2)

    def test_channel_to_discord_format(self) -> None:
        """Channel converts to Discord API format."""
        channel = DiscordTextChannel(
            id=10,
            name="test-channel",
            category_id=None,
            server_id=20,
            position=3,
        )
        result = channel.to_discord_format()
        assert result["id"] == 10
        assert result["name"] == "test-channel"
        assert result["guild_id"] == 20
        assert result["parent_id"] is None
        assert result["position"] == 3


class TestDiscordMessage:
    """Tests for DiscordMessage model."""

    def test_create_message(self) -> None:
        """Message can be created with required fields."""
        now = datetime.utcnow()
        msg = DiscordMessage(
            id=777,
            content="Hello world",
            author_id=888,
            channel_id=999,
            timestamp=now,
        )
        assert msg.id == 777
        assert msg.content == "Hello world"
        assert msg.edited_at is None
        assert msg.timestamp is now

    def test_message_content_max_length(self) -> None:
        """Message content cannot exceed 2000 characters."""
        with pytest.raises(ValidationError):
            DiscordMessage(
                id=1,
                content="a" * 2001,
                author_id=2,
                channel_id=3,
                timestamp=datetime.utcnow(),
            )

    def test_message_to_discord_format(self) -> None:
        """Message converts to Discord API format."""
        now = datetime.utcnow()
        edited = datetime.utcnow()
        msg = DiscordMessage(
            id=10,
            content="Hello",
            author_id=20,
            channel_id=30,
            timestamp=now,
            edited_at=edited,
        )
        result = msg.to_discord_format()
        assert result["id"] == 10
        assert result["content"] == "Hello"
        assert result["author_id"] == 20
        assert result["channel_id"] == 30
        assert result["timestamp"] == now.isoformat()
        assert result["edited_timestamp"] == edited.isoformat()

    def test_message_to_discord_format_with_no_edit(self) -> None:
        """Message includes null edited_timestamp when not edited."""
        now = datetime.utcnow()
        msg = DiscordMessage(
            id=10,
            content="Hello",
            author_id=20,
            channel_id=30,
            timestamp=now,
        )
        result = msg.to_discord_format()
        assert result["edited_timestamp"] is None


class TestDiscordUser:
    """Tests for DiscordUser model."""

    def test_create_user(self) -> None:
        """User can be created with required fields."""
        user = DiscordUser(
            id=555,
            username="testuser",
        )
        assert user.id == 555
        assert user.username == "testuser"
        assert user.bot is False
        assert user.discriminator == "0"
        assert isinstance(user.created_at, datetime)

    def test_create_bot_user(self) -> None:
        """Bot users can be created."""
        bot = DiscordUser(
            id=666,
            username="coolbot",
            bot=True,
        )
        assert bot.bot is True

    def test_user_to_discord_format(self) -> None:
        """User converts to Discord API format."""
        user = DiscordUser(id=1, username="name", discriminator="0", bot=False)
        data = user.to_discord_format()
        assert data["id"] == 1
        assert data["username"] == "name"
        assert data["discriminator"] == "0"
        assert data["bot"] is False
        assert isinstance(data["created_at"], str)


class TestSQLModelIntegration:
    """Tests that SQLModel table configuration works and preserves validation."""

    def test_create_tables(self) -> None:
        """SQLModel can create tables from models."""
        engine = _create_sqlite_engine()
        SQLModel.metadata.create_all(engine)

        tables = SQLModel.metadata.tables
        assert "categories" in tables
        assert "text_channels" in tables
        assert "messages" in tables
        assert "users" in tables

    def test_save_and_retrieve_category(self) -> None:
        """Category can be saved to database and retrieved."""
        engine = _create_sqlite_engine()
        SQLModel.metadata.create_all(engine)

        category = DiscordCategory(id=123, name="Test", server_id=456)

        with Session(engine) as session:
            session.add(category)
            session.commit()

        with Session(engine) as session:
            retrieved = session.get(DiscordCategory, 123)
            assert retrieved is not None
            assert retrieved.name == "Test"
            assert retrieved.server_id == 456

    def test_foreign_key_relationships(self) -> None:
        """Foreign keys support references between tables."""
        engine = _create_sqlite_engine()
        SQLModel.metadata.create_all(engine)

        category = DiscordCategory(id=100, name="Cat", server_id=200)
        channel = DiscordTextChannel(id=300, name="test-channel", category_id=100, server_id=200)

        with Session(engine) as session:
            session.add(category)
            session.add(channel)
            session.commit()

            retrieved_channel = session.get(DiscordTextChannel, 300)
            assert retrieved_channel is not None
            assert retrieved_channel.category_id == 100

    def test_foreign_key_enforcement(self) -> None:
        """Foreign keys prevent inserting rows with missing references."""
        engine = _create_sqlite_engine()
        SQLModel.metadata.create_all(engine)

        # Channel references missing category
        channel = DiscordTextChannel(id=1, name="test-channel", category_id=999, server_id=200)

        with Session(engine) as session:
            session.add(channel)
            with pytest.raises(IntegrityError):
                session.commit()

    def test_indexes_exist(self) -> None:
        """Models declare indexes on commonly queried fields."""
        engine = _create_sqlite_engine()
        SQLModel.metadata.create_all(engine)

        inspector = inspect(engine)

        category_indexes = inspector.get_indexes("categories")
        category_cols = {col for idx in category_indexes for col in idx.get("column_names", [])}
        assert "name" in category_cols
        assert "server_id" in category_cols

        channel_indexes = inspector.get_indexes("text_channels")
        channel_cols = {col for idx in channel_indexes for col in idx.get("column_names", [])}
        assert "name" in channel_cols
        assert "server_id" in channel_cols

        message_indexes = inspector.get_indexes("messages")
        message_cols = {col for idx in message_indexes for col in idx.get("column_names", [])}
        assert "channel_id" in message_cols
        assert "timestamp" in message_cols
        assert "author_id" in message_cols

        user_indexes = inspector.get_indexes("users")
        user_cols = {col for idx in user_indexes for col in idx.get("column_names", [])}
        assert "username" in user_cols
