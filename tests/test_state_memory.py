# tests/test_state_memory.py
from __future__ import annotations

from datetime import datetime

import pytest

from discordia.exceptions import StateError
from discordia.state.memory import MemoryState
from discordia.state.models import Category, Channel, Message, User


@pytest.mark.asyncio
async def test_save_and_get_category():
    """Categories can be saved and retrieved."""
    state = MemoryState()
    category = Category(
        id=123456789012345678,
        name="Test Category",
        server_id=987654321098765432,
    )

    await state.save_category(category)
    retrieved = await state.get_category(123456789012345678)

    assert retrieved is not None
    assert retrieved.id == category.id
    assert retrieved.name == category.name


@pytest.mark.asyncio
async def test_get_nonexistent_category():
    """Getting nonexistent category returns None."""
    state = MemoryState()
    result = await state.get_category(999999999999999999)
    assert result is None


@pytest.mark.asyncio
async def test_save_and_get_channel():
    """Channels can be saved and retrieved."""
    state = MemoryState()
    category = Category(
        id=123456789012345678,
        name="Test Category",
        server_id=987654321098765432,
    )
    await state.save_category(category)

    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        category_id=123456789012345678,
        server_id=987654321098765432,
    )
    await state.save_channel(channel)

    retrieved = await state.get_channel(111222333444555666)
    assert retrieved is not None
    assert retrieved.id == channel.id
    assert retrieved.name == channel.name


@pytest.mark.asyncio
async def test_save_channel_without_category():
    """Channels can be saved without a category."""
    state = MemoryState()
    channel = Channel(
        id=111222333444555666,
        name="uncategorized",
        server_id=987654321098765432,
        category_id=None,
    )
    await state.save_channel(channel)

    retrieved = await state.get_channel(111222333444555666)
    assert retrieved is not None
    assert retrieved.category_id is None


@pytest.mark.asyncio
async def test_save_channel_invalid_category():
    """Saving channel with nonexistent category raises error."""
    state = MemoryState()
    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        category_id=999999999999999999,
        server_id=987654321098765432,
    )

    with pytest.raises(StateError, match="Category .* not found"):
        await state.save_channel(channel)


@pytest.mark.asyncio
async def test_save_and_get_user():
    """Users can be saved and retrieved."""
    state = MemoryState()
    user = User(
        id=999888777666555444,
        username="TestUser",
    )
    await state.save_user(user)

    retrieved = await state.get_user(999888777666555444)
    assert retrieved is not None
    assert retrieved.id == user.id
    assert retrieved.username == user.username


@pytest.mark.asyncio
async def test_save_message():
    """Messages can be saved."""
    state = MemoryState()

    user = User(id=999888777666555444, username="TestUser")
    await state.save_user(user)

    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        server_id=987654321098765432,
    )
    await state.save_channel(channel)

    message = Message(
        id=555666777888999000,
        content="Test message",
        author_id=999888777666555444,
        channel_id=111222333444555666,
        timestamp=datetime.utcnow(),
    )
    await state.save_message(message)

    messages = await state.get_messages(111222333444555666)
    assert len(messages) == 1
    assert messages[0].content == "Test message"


@pytest.mark.asyncio
async def test_save_message_invalid_author():
    """Saving message with nonexistent author raises error."""
    state = MemoryState()

    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        server_id=987654321098765432,
    )
    await state.save_channel(channel)

    message = Message(
        id=555666777888999000,
        content="Test message",
        author_id=999999999999999999,
        channel_id=111222333444555666,
        timestamp=datetime.utcnow(),
    )

    with pytest.raises(StateError, match="User .* not found"):
        await state.save_message(message)


@pytest.mark.asyncio
async def test_save_message_invalid_channel():
    """Saving message with nonexistent channel raises error."""
    state = MemoryState()

    user = User(id=999888777666555444, username="TestUser")
    await state.save_user(user)

    message = Message(
        id=555666777888999000,
        content="Test message",
        author_id=999888777666555444,
        channel_id=999999999999999999,
        timestamp=datetime.utcnow(),
    )

    with pytest.raises(StateError, match="Channel .* not found"):
        await state.save_message(message)


@pytest.mark.asyncio
async def test_get_messages_ordered():
    """Messages are returned ordered by timestamp."""
    state = MemoryState()

    user = User(id=999888777666555444, username="TestUser")
    await state.save_user(user)

    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        server_id=987654321098765432,
    )
    await state.save_channel(channel)

    base_time = datetime.utcnow()
    messages_data = [
        (555666777888999001, "Message 1", base_time),
        (555666777888999002, "Message 2", base_time),
        (555666777888999003, "Message 3", base_time),
    ]

    for msg_id, content, timestamp in messages_data:
        message = Message(
            id=msg_id,
            content=content,
            author_id=999888777666555444,
            channel_id=111222333444555666,
            timestamp=timestamp,
        )
        await state.save_message(message)

    messages = await state.get_messages(111222333444555666)
    assert len(messages) == 3
    assert messages[0].content == "Message 1"
    assert messages[1].content == "Message 2"
    assert messages[2].content == "Message 3"


@pytest.mark.asyncio
async def test_get_messages_with_limit():
    """Messages can be retrieved with a limit."""
    state = MemoryState()

    user = User(id=999888777666555444, username="TestUser")
    await state.save_user(user)

    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        server_id=987654321098765432,
    )
    await state.save_channel(channel)

    base_time = datetime.utcnow()
    for i in range(10):
        message = Message(
            id=555666777888999000 + i,
            content=f"Message {i}",
            author_id=999888777666555444,
            channel_id=111222333444555666,
            timestamp=base_time,
        )
        await state.save_message(message)

    messages = await state.get_messages(111222333444555666, limit=5)
    assert len(messages) == 5
    assert messages[-1].content == "Message 9"


@pytest.mark.asyncio
async def test_update_entity():
    """Saving entity with same ID updates it."""
    state = MemoryState()

    user = User(id=999888777666555444, username="OriginalName")
    await state.save_user(user)

    updated_user = User(id=999888777666555444, username="UpdatedName")
    await state.save_user(updated_user)

    retrieved = await state.get_user(999888777666555444)
    assert retrieved.username == "UpdatedName"
