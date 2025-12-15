# tests/conftest.py
from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

import pytest

from discordia.settings import Settings
from discordia.state.memory import MemoryState
from discordia.state.models import Category, Channel, Message, User
from discordia.state.registry import EntityRegistry
from discordia.types import DiscordSnowflake


@pytest.fixture
def test_server_id() -> DiscordSnowflake:
    """Standard test server ID."""
    return 123456789012345678


@pytest.fixture
def test_category_id() -> DiscordSnowflake:
    """Standard test category ID."""
    return 987654321098765432


@pytest.fixture
def test_channel_id() -> DiscordSnowflake:
    """Standard test channel ID."""
    return 111222333444555666


@pytest.fixture
def test_user_id() -> DiscordSnowflake:
    """Standard test user ID."""
    return 999888777666555444


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Create test settings with minimal config."""
    jsonl_path = tmp_path / "test_state.jsonl"
    return Settings(
        discord_token="test_token_123",
        server_id=123456789012345678,
        jsonl_path=str(jsonl_path),
        persistence_enabled=False,
        _env_file=None,
    )


@pytest.fixture
async def memory_state() -> AsyncIterator[MemoryState]:
    """Create fresh memory state for testing."""
    state = MemoryState()
    yield state


@pytest.fixture
async def populated_state(
    memory_state: MemoryState,
    test_server_id: DiscordSnowflake,
    test_category_id: DiscordSnowflake,
    test_channel_id: DiscordSnowflake,
    test_user_id: DiscordSnowflake,
) -> MemoryState:
    """Memory state with sample data."""
    category = Category(
        id=test_category_id,
        name="Test Category",
        server_id=test_server_id,
        position=0,
    )
    await memory_state.save_category(category)

    channel = Channel(
        id=test_channel_id,
        name="test-channel",
        category_id=test_category_id,
        server_id=test_server_id,
        position=0,
        topic="Test topic",
    )
    await memory_state.save_channel(channel)

    user = User(
        id=test_user_id,
        username="TestUser",
        bot=False,
    )
    await memory_state.save_user(user)

    message = Message(
        id=555666777888999000,
        content="Test message",
        author_id=test_user_id,
        channel_id=test_channel_id,
        timestamp=datetime.utcnow(),
    )
    await memory_state.save_message(message)

    return memory_state


@pytest.fixture
async def entity_registry(memory_state: MemoryState) -> EntityRegistry:
    """Create entity registry with memory state."""
    return EntityRegistry(memory_state)
