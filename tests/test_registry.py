# tests/test_registry.py
from __future__ import annotations

import pytest

from discordia.exceptions import EntityNotFoundError
from discordia.registry import EntityRegistry
from discordia.state import Category, Channel, MemoryState


@pytest.mark.asyncio
async def test_get_category_by_name() -> None:
    state = MemoryState()
    registry = EntityRegistry(state)

    cat = Category(id=123, name="General", server_id=456)
    await state.save_category(cat)

    found = await registry.get_category_by_name("General", 456)
    assert found == cat


@pytest.mark.asyncio
async def test_get_category_by_name_not_found() -> None:
    state = MemoryState()
    registry = EntityRegistry(state)

    with pytest.raises(EntityNotFoundError):
        await registry.get_category_by_name("Missing", 456)


@pytest.mark.asyncio
async def test_get_channel_by_name() -> None:
    state = MemoryState()
    registry = EntityRegistry(state)

    ch = Channel(id=789, name="general", server_id=456)
    await state.save_channel(ch)

    found = await registry.get_channel_by_name("general", 456)
    assert found == ch


@pytest.mark.asyncio
async def test_get_channel_by_name_not_found() -> None:
    state = MemoryState()
    registry = EntityRegistry(state)

    with pytest.raises(EntityNotFoundError):
        await registry.get_channel_by_name("missing", 456)


@pytest.mark.asyncio
async def test_get_channels_in_category() -> None:
    state = MemoryState()
    registry = EntityRegistry(state)

    cat = Category(id=123, name="General", server_id=456)
    await state.save_category(cat)

    ch1 = Channel(id=789, name="general", server_id=456, category_id=123)
    ch2 = Channel(id=790, name="random", server_id=456, category_id=123)
    await state.save_channel(ch1)
    await state.save_channel(ch2)

    channels = await registry.get_channels_in_category(123)
    assert len(channels) == 2
    assert ch1 in channels
    assert ch2 in channels
