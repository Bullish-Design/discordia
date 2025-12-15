# tests/test_state_models.py
from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from discordia.state.models import Category, Channel, Message, User


def test_category_creation():
    """Category can be created with valid data."""
    category = Category(
        id=123456789012345678,
        name="Test Category",
        server_id=987654321098765432,
        position=0,
    )
    assert category.id == 123456789012345678
    assert category.name == "Test Category"
    assert category.server_id == 987654321098765432
    assert category.position == 0
    assert isinstance(category.created_at, datetime)


def test_category_invalid_id():
    """Category rejects invalid snowflake IDs."""
    with pytest.raises(ValidationError):
        Category(
            id=0,
            name="Test",
            server_id=123456789012345678,
        )


def test_channel_creation():
    """Channel can be created with valid data."""
    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        category_id=123456789012345678,
        server_id=987654321098765432,
        position=1,
        topic="Test topic",
    )
    assert channel.id == 111222333444555666
    assert channel.name == "test-channel"
    assert channel.category_id == 123456789012345678
    assert channel.server_id == 987654321098765432
    assert channel.position == 1
    assert channel.topic == "Test topic"


def test_channel_without_category():
    """Channel can be created without a category."""
    channel = Channel(
        id=111222333444555666,
        name="uncategorized",
        server_id=987654321098765432,
    )
    assert channel.category_id is None


def test_channel_invalid_category_id():
    """Channel rejects invalid category IDs."""
    with pytest.raises(ValidationError):
        Channel(
            id=111222333444555666,
            name="test-channel",
            category_id=0,
            server_id=987654321098765432,
        )


def test_channel_topic_max_length():
    """Channel topic has 1024 character limit."""
    channel = Channel(
        id=111222333444555666,
        name="test-channel",
        server_id=987654321098765432,
        topic="a" * 1024,
    )
    assert len(channel.topic) == 1024

    with pytest.raises(ValidationError):
        Channel(
            id=111222333444555666,
            name="test-channel",
            server_id=987654321098765432,
            topic="a" * 1025,
        )


def test_user_creation():
    """User can be created with valid data."""
    user = User(
        id=999888777666555444,
        username="TestUser",
        discriminator="1234",
        bot=False,
    )
    assert user.id == 999888777666555444
    assert user.username == "TestUser"
    assert user.discriminator == "1234"
    assert user.bot is False


def test_user_defaults():
    """User uses sensible defaults."""
    user = User(
        id=999888777666555444,
        username="TestUser",
    )
    assert user.discriminator == "0"
    assert user.bot is False


def test_message_creation():
    """Message can be created with valid data."""
    timestamp = datetime.utcnow()
    message = Message(
        id=555666777888999000,
        content="Test message",
        author_id=999888777666555444,
        channel_id=111222333444555666,
        timestamp=timestamp,
    )
    assert message.id == 555666777888999000
    assert message.content == "Test message"
    assert message.author_id == 999888777666555444
    assert message.channel_id == 111222333444555666
    assert message.timestamp == timestamp
    assert message.edited_at is None


def test_message_content_max_length():
    """Message content enforces 2000 character limit."""
    timestamp = datetime.utcnow()
    message = Message(
        id=555666777888999000,
        content="a" * 2000,
        author_id=999888777666555444,
        channel_id=111222333444555666,
        timestamp=timestamp,
    )
    assert len(message.content) == 2000

    with pytest.raises(ValidationError):
        Message(
            id=555666777888999000,
            content="a" * 2001,
            author_id=999888777666555444,
            channel_id=111222333444555666,
            timestamp=timestamp,
        )


def test_message_with_edit():
    """Message can track edits."""
    timestamp = datetime.utcnow()
    edited = datetime.utcnow()
    message = Message(
        id=555666777888999000,
        content="Edited message",
        author_id=999888777666555444,
        channel_id=111222333444555666,
        timestamp=timestamp,
        edited_at=edited,
    )
    assert message.edited_at == edited
