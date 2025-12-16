# tests/test_types.py
from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from discordia.types import ChannelName, DiscordID, MessageContent, Username


class DiscordIdModel(BaseModel):
    id: DiscordID


def test_discord_id_valid() -> None:
    model = DiscordIdModel(id=123456789)
    assert model.id == 123456789


def test_discord_id_negative() -> None:
    with pytest.raises(ValidationError):
        DiscordIdModel(id=-1)


def test_discord_id_zero() -> None:
    with pytest.raises(ValidationError):
        DiscordIdModel(id=0)


def test_discord_id_too_large() -> None:
    with pytest.raises(ValidationError):
        DiscordIdModel(id=2**63)


class ChannelModel(BaseModel):
    name: ChannelName


def test_channel_name_valid() -> None:
    assert ChannelModel(name="general").name == "general"
    assert ChannelModel(name="test-channel").name == "test-channel"
    assert ChannelModel(name="bot_commands").name == "bot_commands"


def test_channel_name_uppercase() -> None:
    with pytest.raises(ValidationError):
        ChannelModel(name="General")


def test_channel_name_special_chars() -> None:
    with pytest.raises(ValidationError):
        ChannelModel(name="channel#1")


def test_channel_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ChannelModel(name="a" * 101)


class UsernameModel(BaseModel):
    username: Username


def test_username_valid() -> None:
    assert UsernameModel(username="Alice").username == "Alice"


def test_username_too_short() -> None:
    with pytest.raises(ValidationError):
        UsernameModel(username="a")


def test_username_too_long() -> None:
    with pytest.raises(ValidationError):
        UsernameModel(username="a" * 33)


class MessageModel(BaseModel):
    content: MessageContent


def test_message_content_valid() -> None:
    msg = MessageModel(content="Hello world")
    assert msg.content == "Hello world"


def test_message_content_too_long() -> None:
    with pytest.raises(ValidationError):
        MessageModel(content="a" * 2001)
