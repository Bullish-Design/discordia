# tests/test_discovery.py
from __future__ import annotations

from unittest.mock import Mock

import pytest

from discordia.discovery import DiscoveryEngine, GuildCategory, GuildText
from discordia.exceptions import DiscordAPIError
from discordia.state import Category, MemoryState


def create_mock_category(channel_id: int, name: str, position: int = 0) -> Mock:
    """Create a mock Discord category channel."""

    cat = Mock()
    cat.id = channel_id
    cat.name = name
    cat.position = position
    cat.__class__ = GuildCategory
    return cat


def create_mock_text_channel(channel_id: int, name: str, parent_id: int | None = None) -> Mock:
    """Create a mock Discord text channel."""

    ch = Mock()
    ch.id = channel_id
    ch.name = name
    ch.parent_id = parent_id
    ch.position = 0
    ch.topic = None
    ch.__class__ = GuildText
    return ch


@pytest.mark.asyncio
async def test_discover_categories_saves_to_store() -> None:
    state = MemoryState()
    engine = DiscoveryEngine(state, server_id=456)

    guild = Mock()
    guild.channels = [create_mock_category(123, "General")]

    categories = await engine.discover_categories(guild)

    assert len(categories) == 1
    assert categories[0].id == 123
    assert categories[0].name == "General"

    saved = await state.get_category(123)
    assert saved is not None
    assert saved.name == "General"


@pytest.mark.asyncio
async def test_discover_channels_saves_to_store() -> None:
    state = MemoryState()
    engine = DiscoveryEngine(state, server_id=456)

    guild = Mock()
    guild.channels = [create_mock_text_channel(789, "general")]

    channels = await engine.discover_channels(guild)

    assert len(channels) == 1
    assert channels[0].id == 789
    assert channels[0].name == "general"

    saved = await state.get_channel(789)
    assert saved is not None


@pytest.mark.asyncio
async def test_discover_channels_with_category_requires_existing_category() -> None:
    state = MemoryState()
    engine = DiscoveryEngine(state, server_id=456)

    await state.save_category(Category(id=123, name="General", server_id=456))

    guild = Mock()
    guild.channels = [create_mock_text_channel(789, "general", parent_id=123)]

    channels = await engine.discover_channels(guild)
    assert channels[0].category_id == 123


@pytest.mark.asyncio
async def test_discovery_wraps_errors_in_discord_api_error() -> None:
    state = MemoryState()
    engine = DiscoveryEngine(state, server_id=456)

    # A text channel with a missing category triggers a StateError from the store, which should be wrapped.
    guild = Mock()
    guild.channels = [create_mock_text_channel(789, "general", parent_id=999)]

    with pytest.raises(DiscordAPIError):
        await engine.discover_channels(guild)
