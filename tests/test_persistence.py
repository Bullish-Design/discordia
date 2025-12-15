# tests/test_persistence.py
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from discordia.exceptions import DatabaseError
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.models.user import DiscordUser
from discordia.persistence.database import DatabaseWriter


@pytest.fixture
async def db_writer() -> DatabaseWriter:
    """Create in-memory database writer for testing."""
    writer = DatabaseWriter("sqlite+aiosqlite:///:memory:")
    await writer.initialize()
    yield writer
    await writer.close()


@pytest.mark.asyncio
async def test_initialize_creates_tables(db_writer: DatabaseWriter) -> None:
    """Database initialization creates all tables."""
    assert db_writer._initialized is True


@pytest.mark.asyncio
async def test_save_and_retrieve_category(db_writer: DatabaseWriter) -> None:
    """Category can be saved and retrieved."""
    category = DiscordCategory(id=1, name="Test", server_id=100)
    await db_writer.save_category(category)

    retrieved = await db_writer.get_category(1)
    assert retrieved is not None
    assert retrieved.name == "Test"
    assert retrieved.server_id == 100


@pytest.mark.asyncio
async def test_get_category_by_name(db_writer: DatabaseWriter) -> None:
    """Category can be queried by name within a server."""

    category = DiscordCategory(id=2, name="Log", server_id=200)
    await db_writer.save_category(category)

    found = await db_writer.get_category_by_name("Log", 200)
    assert found is not None
    assert found.id == 2
    assert found.name == "Log"

    missing = await db_writer.get_category_by_name("Missing", 200)
    assert missing is None


@pytest.mark.asyncio
async def test_save_and_retrieve_channel(db_writer: DatabaseWriter) -> None:
    """Channel can be saved and retrieved."""
    channel = DiscordTextChannel(
        id=2,
        name="test-channel",
        server_id=100,
    )
    await db_writer.save_channel(channel)

    retrieved = await db_writer.get_channel(2)
    assert retrieved is not None
    assert retrieved.name == "test-channel"


@pytest.mark.asyncio
async def test_save_message(db_writer: DatabaseWriter) -> None:
    """Message can be saved."""
    user = DiscordUser(id=10, username="testuser")
    await db_writer.save_user(user)

    channel = DiscordTextChannel(id=20, name="test", server_id=100)
    await db_writer.save_channel(channel)

    message = DiscordMessage(
        id=30,
        content="Hello",
        author_id=10,
        channel_id=20,
        timestamp=datetime.utcnow(),
    )
    await db_writer.save_message(message)

    retrieved = await db_writer.get_messages(20, limit=10)
    assert len(retrieved) == 1
    assert retrieved[0].content == "Hello"


@pytest.mark.asyncio
async def test_get_messages_returns_ordered_list(db_writer: DatabaseWriter) -> None:
    """get_messages returns messages in chronological order."""
    user = DiscordUser(id=10, username="test")
    await db_writer.save_user(user)

    channel = DiscordTextChannel(id=20, name="test", server_id=100)
    await db_writer.save_channel(channel)

    base = datetime.utcnow()
    msg1 = DiscordMessage(id=1, content="First", author_id=10, channel_id=20, timestamp=base)
    msg2 = DiscordMessage(id=2, content="Second", author_id=10, channel_id=20, timestamp=base + timedelta(seconds=1))
    msg3 = DiscordMessage(id=3, content="Third", author_id=10, channel_id=20, timestamp=base + timedelta(seconds=2))

    await db_writer.save_message(msg3)
    await db_writer.save_message(msg1)
    await db_writer.save_message(msg2)

    messages = await db_writer.get_messages(20, limit=10)
    assert len(messages) == 3
    assert [m.content for m in messages] == ["First", "Second", "Third"]


@pytest.mark.asyncio
async def test_get_messages_respects_limit(db_writer: DatabaseWriter) -> None:
    """get_messages respects limit parameter."""
    user = DiscordUser(id=10, username="test")
    await db_writer.save_user(user)

    channel = DiscordTextChannel(id=20, name="test", server_id=100)
    await db_writer.save_channel(channel)

    base = datetime.utcnow()
    for i in range(10):
        msg = DiscordMessage(
            id=i + 1,
            content=f"Message {i}",
            author_id=10,
            channel_id=20,
            timestamp=base + timedelta(seconds=i),
        )
        await db_writer.save_message(msg)

    messages = await db_writer.get_messages(20, limit=5)
    assert len(messages) == 5
    assert messages[0].content == "Message 5"
    assert messages[-1].content == "Message 9"


@pytest.mark.asyncio
async def test_database_error_on_invalid_operation(db_writer: DatabaseWriter) -> None:
    """Database errors are wrapped in DatabaseError."""
    message = DiscordMessage(
        id=999,
        content="Invalid",
        author_id=99999,
        channel_id=88888,
        timestamp=datetime.utcnow(),
    )

    with pytest.raises(DatabaseError) as exc_info:
        await db_writer.save_message(message)

    assert "Failed to save message" in str(exc_info.value)
