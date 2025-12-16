# tests/test_state.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from discordia.exceptions import StateError
from discordia.state import Category, Channel, MemoryState, Message, User


@pytest.mark.asyncio
async def test_category_creation() -> None:
    cat = Category(id=123, name="General", server_id=456)
    assert cat.id == 123
    assert cat.name == "General"
    assert cat.position == 0


@pytest.mark.asyncio
async def test_channel_creation() -> None:
    ch = Channel(id=789, name="general", server_id=456)
    assert ch.name == "general"
    assert ch.is_categorized is False


@pytest.mark.asyncio
async def test_channel_with_category() -> None:
    ch = Channel(id=789, name="general", server_id=456, category_id=123)
    assert ch.is_categorized is True


@pytest.mark.asyncio
async def test_user_creation() -> None:
    user = User(id=111, username="Alice")
    assert user.username == "Alice"
    assert user.bot is False


@pytest.mark.asyncio
async def test_message_computed_fields() -> None:
    msg = Message(
        id=999,
        content="Hello",
        author_id=111,
        channel_id=789,
        timestamp=datetime.now(UTC) - timedelta(seconds=10),
    )
    assert msg.age_seconds >= 10
    assert msg.is_edited is False


@pytest.mark.asyncio
async def test_message_edited() -> None:
    msg = Message(
        id=999,
        content="Hello",
        author_id=111,
        channel_id=789,
        timestamp=datetime.now(UTC),
        edited_at=datetime.now(UTC),
    )
    assert msg.is_edited is True


@pytest.mark.asyncio
async def test_memory_state_save_category() -> None:
    state = MemoryState()
    cat = Category(id=123, name="General", server_id=456)

    await state.save_category(cat)
    retrieved = await state.get_category(123)

    assert retrieved == cat


@pytest.mark.asyncio
async def test_memory_state_save_channel() -> None:
    state = MemoryState()
    cat = Category(id=123, name="General", server_id=456)
    await state.save_category(cat)

    ch = Channel(id=789, name="general", server_id=456, category_id=123)
    await state.save_channel(ch)

    retrieved = await state.get_channel(789)
    assert retrieved == ch


@pytest.mark.asyncio
async def test_memory_state_channel_invalid_category() -> None:
    state = MemoryState()
    ch = Channel(id=789, name="general", server_id=456, category_id=999)

    with pytest.raises(StateError):
        await state.save_channel(ch)


@pytest.mark.asyncio
async def test_memory_state_message_validation() -> None:
    state = MemoryState()
    msg = Message(
        id=999,
        content="Hello",
        author_id=111,
        channel_id=789,
        timestamp=datetime.now(UTC),
    )

    with pytest.raises(StateError):
        await state.save_message(msg)

    user = User(id=111, username="Alice")
    await state.save_user(user)

    with pytest.raises(StateError):
        await state.save_message(msg)

    ch = Channel(id=789, name="general", server_id=456)
    await state.save_channel(ch)

    await state.save_message(msg)
    retrieved = await state.get_message(999)
    assert retrieved == msg


@pytest.mark.asyncio
async def test_memory_state_get_messages() -> None:
    state = MemoryState()

    user = User(id=111, username="Alice")
    await state.save_user(user)
    ch = Channel(id=789, name="general", server_id=456)
    await state.save_channel(ch)

    now = datetime.now(UTC)
    for i in range(5):
        msg = Message(
            id=1000 + i,
            content=f"Message {i}",
            author_id=111,
            channel_id=789,
            timestamp=now + timedelta(milliseconds=i),
        )
        await state.save_message(msg)

    messages = await state.get_messages(789, limit=3)
    assert len(messages) == 3
    assert messages[0].content == "Message 2"


@pytest.mark.asyncio
async def test_state_entity_timestamp_update() -> None:
    cat = Category(id=123, name="General", server_id=456)
    original_updated = cat.updated_at

    cat = Category.model_validate(cat.model_dump() | {"name": "Updated"})
    assert cat.updated_at >= original_updated
