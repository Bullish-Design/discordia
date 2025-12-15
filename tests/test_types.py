# tests/test_types.py
from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from discordia.types import (
    CategoryName,
    ChannelName,
    DiscordSnowflake,
    MessageContent,
    Username,
)


class SnowflakeModel(BaseModel):
    id: DiscordSnowflake


class ChannelModel(BaseModel):
    name: ChannelName


class CategoryModel(BaseModel):
    name: CategoryName


class MessageModel(BaseModel):
    content: MessageContent


class UserModel(BaseModel):
    username: Username


def test_discord_snowflake_valid():
    """Discord snowflake accepts positive integers."""
    model = SnowflakeModel(id=123456789012345678)
    assert model.id == 123456789012345678


def test_discord_snowflake_invalid():
    """Discord snowflake rejects non-positive integers."""
    with pytest.raises(ValidationError):
        SnowflakeModel(id=0)

    with pytest.raises(ValidationError):
        SnowflakeModel(id=-1)


def test_channel_name_valid():
    """Channel name accepts lowercase, hyphens, numbers."""
    model = ChannelModel(name="test-channel-123")
    assert model.name == "test-channel-123"


def test_channel_name_invalid_uppercase():
    """Channel name rejects uppercase letters."""
    with pytest.raises(ValidationError):
        ChannelModel(name="Test-Channel")


def test_channel_name_invalid_spaces():
    """Channel name rejects spaces."""
    with pytest.raises(ValidationError):
        ChannelModel(name="test channel")


def test_channel_name_invalid_special_chars():
    """Channel name rejects special characters."""
    with pytest.raises(ValidationError):
        ChannelModel(name="test@channel")


def test_channel_name_length_limits():
    """Channel name enforces 1-100 character limit."""
    with pytest.raises(ValidationError):
        ChannelModel(name="")

    with pytest.raises(ValidationError):
        ChannelModel(name="a" * 101)

    # Boundaries are valid
    model = ChannelModel(name="a")
    assert model.name == "a"

    model = ChannelModel(name="a" * 100)
    assert len(model.name) == 100


def test_category_name_valid():
    """Category name accepts various formats."""
    model = CategoryModel(name="Test Category")
    assert model.name == "Test Category"

    model = CategoryModel(name="CATEGORY-123")
    assert model.name == "CATEGORY-123"


def test_category_name_length_limits():
    """Category name enforces 1-100 character limit."""
    with pytest.raises(ValidationError):
        CategoryModel(name="")

    with pytest.raises(ValidationError):
        CategoryModel(name="a" * 101)


def test_message_content_valid():
    """Message content accepts strings up to 2000 chars."""
    model = MessageModel(content="Hello, world!")
    assert model.content == "Hello, world!"


def test_message_content_length_limit():
    """Message content enforces 2000 character limit."""
    with pytest.raises(ValidationError):
        MessageModel(content="a" * 2001)

    # Boundary is valid
    model = MessageModel(content="a" * 2000)
    assert len(model.content) == 2000


def test_username_valid():
    """Username accepts strings between 2-32 chars."""
    model = UserModel(username="TestUser")
    assert model.username == "TestUser"


def test_username_length_limits():
    """Username enforces 2-32 character limit."""
    with pytest.raises(ValidationError):
        UserModel(username="a")

    with pytest.raises(ValidationError):
        UserModel(username="a" * 33)

    # Boundaries are valid
    model = UserModel(username="ab")
    assert model.username == "ab"

    model = UserModel(username="a" * 32)
    assert len(model.username) == 32
