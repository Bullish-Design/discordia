# tests/test_state_registry.py
from __future__ import annotations

import pytest

from discordia.exceptions import CategoryNotFoundError, ChannelNotFoundError
from discordia.state.models import Category, Channel


@pytest.mark.asyncio
async def test_get_category_by_name(populated_state, entity_registry, test_server_id):
    """Registry can find categories by name."""
    category = await entity_registry.get_category_by_name("Test Category", test_server_id)
    assert category.name == "Test Category"


@pytest.mark.asyncio
async def test_get_category_by_name_not_found(entity_registry, test_server_id):
    """Registry raises error when category not found."""
    with pytest.raises(CategoryNotFoundError, match="not found"):
        await entity_registry.get_category_by_name("Nonexistent", test_server_id)


@pytest.mark.asyncio
async def test_get_channel_by_name(populated_state, entity_registry, test_server_id):
    """Registry can find channels by name."""
    channel = await entity_registry.get_channel_by_name("test-channel", test_server_id)
    assert channel.name == "test-channel"


@pytest.mark.asyncio
async def test_get_channel_by_name_not_found(entity_registry, test_server_id):
    """Registry raises error when channel not found."""
    with pytest.raises(ChannelNotFoundError, match="not found"):
        await entity_registry.get_channel_by_name("nonexistent", test_server_id)


@pytest.mark.asyncio
async def test_get_channels_in_category(
    memory_state, entity_registry, test_server_id, test_category_id
):
    """Registry can find all channels in a category."""
    category = Category(
        id=test_category_id,
        name="Test Category",
        server_id=test_server_id,
    )
    await memory_state.save_category(category)

    channels_data = [
        (111111111111111111, "channel-1"),
        (222222222222222222, "channel-2"),
        (333333333333333333, "channel-3"),
    ]

    for channel_id, name in channels_data:
        channel = Channel(
            id=channel_id,
            name=name,
            category_id=test_category_id,
            server_id=test_server_id,
        )
        await memory_state.save_channel(channel)

    channels = await entity_registry.get_channels_in_category(test_category_id)
    assert len(channels) == 3
    assert all(c.category_id == test_category_id for c in channels)


@pytest.mark.asyncio
async def test_get_channels_in_empty_category(entity_registry, test_category_id):
    """Registry returns empty list for category with no channels."""
    channels = await entity_registry.get_channels_in_category(test_category_id)
    assert channels == []
