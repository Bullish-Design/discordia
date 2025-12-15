# tests/test_templates.py
from __future__ import annotations

import pytest
from pydantic import ValidationError

from discordia.templates.base import TemplateModel
from discordia.templates.category import CategoryTemplate
from discordia.templates.channel import (
    AnnouncementChannelTemplate,
    ChannelType,
    ForumChannelTemplate,
    TextChannelTemplate,
    VoiceChannelTemplate,
)
from discordia.templates.server import ServerTemplate


def test_template_model_frozen():
    """Template models are immutable."""

    class TestTemplate(TemplateModel):
        value: str

    template = TestTemplate(value="test")
    with pytest.raises(ValidationError):
        template.value = "modified"


def test_template_model_forbid_extra():
    """Template models reject extra fields."""

    class TestTemplate(TemplateModel):
        value: str

    with pytest.raises(ValidationError):
        TestTemplate(value="test", extra_field="not allowed")


def test_text_channel_template():
    """TextChannelTemplate can be created with valid data."""
    channel = TextChannelTemplate(
        name="test-channel",
        topic="Test topic",
        position=0,
        slowmode_seconds=10,
        nsfw=False,
    )
    assert channel.name == "test-channel"
    assert channel.type == ChannelType.TEXT
    assert channel.topic == "Test topic"
    assert channel.slowmode_seconds == 10
    assert channel.nsfw is False


def test_text_channel_defaults():
    """TextChannelTemplate uses sensible defaults."""
    channel = TextChannelTemplate(name="test-channel")
    assert channel.type == ChannelType.TEXT
    assert channel.topic is None
    assert channel.position is None
    assert channel.slowmode_seconds == 0
    assert channel.nsfw is False


def test_text_channel_slowmode_validation():
    """TextChannelTemplate validates slowmode seconds."""
    with pytest.raises(ValidationError):
        TextChannelTemplate(name="test", slowmode_seconds=-1)

    with pytest.raises(ValidationError):
        TextChannelTemplate(name="test", slowmode_seconds=21601)


def test_voice_channel_template():
    """VoiceChannelTemplate can be created."""
    channel = VoiceChannelTemplate(
        name="voice-channel",
        bitrate=128000,
        user_limit=10,
    )
    assert channel.name == "voice-channel"
    assert channel.type == ChannelType.VOICE
    assert channel.bitrate == 128000
    assert channel.user_limit == 10


def test_voice_channel_defaults():
    """VoiceChannelTemplate uses sensible defaults."""
    channel = VoiceChannelTemplate(name="voice")
    assert channel.bitrate == 64000
    assert channel.user_limit == 0


def test_voice_channel_bitrate_validation():
    """VoiceChannelTemplate validates bitrate."""
    with pytest.raises(ValidationError):
        VoiceChannelTemplate(name="voice", bitrate=7999)

    with pytest.raises(ValidationError):
        VoiceChannelTemplate(name="voice", bitrate=384001)


def test_forum_channel_template():
    """ForumChannelTemplate can be created."""
    channel = ForumChannelTemplate(
        name="forum-channel",
        default_thread_slowmode=60,
    )
    assert channel.name == "forum-channel"
    assert channel.type == ChannelType.FORUM
    assert channel.default_thread_slowmode == 60


def test_announcement_channel_template():
    """AnnouncementChannelTemplate can be created."""
    channel = AnnouncementChannelTemplate(name="announcements")
    assert channel.name == "announcements"
    assert channel.type == ChannelType.ANNOUNCEMENT


def test_category_template():
    """CategoryTemplate can be created with channels."""
    channels = [
        TextChannelTemplate(name="text-1"),
        TextChannelTemplate(name="text-2"),
    ]
    category = CategoryTemplate(
        name="Test Category",
        position=0,
        channels=channels,
    )
    assert category.name == "Test Category"
    assert len(category.channels) == 2


def test_category_template_defaults():
    """CategoryTemplate uses sensible defaults."""
    category = CategoryTemplate(name="Test")
    assert category.position is None
    assert category.channels == []


def test_server_template():
    """ServerTemplate can be created with structure."""
    category = CategoryTemplate(
        name="General",
        channels=[TextChannelTemplate(name="general")],
    )
    server = ServerTemplate(
        categories=[category],
        uncategorized_channels=[TextChannelTemplate(name="lobby")],
    )
    assert len(server.categories) == 1
    assert len(server.uncategorized_channels) == 1


def test_server_template_defaults():
    """ServerTemplate uses empty lists as defaults."""
    server = ServerTemplate()
    assert server.categories == []
    assert server.uncategorized_channels == []
    assert server.patterns == []


def test_channel_topic_max_length():
    """Channel topic enforces 1024 character limit."""
    with pytest.raises(ValidationError):
        TextChannelTemplate(name="test", topic="a" * 1025)

    channel = TextChannelTemplate(name="test", topic="a" * 1024)
    assert len(channel.topic) == 1024
