# tests/test_managers.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.exceptions import CategoryNotFoundError, ChannelNotFoundError
from discordia.managers.category_manager import CategoryManager
from discordia.managers.channel_manager import ChannelManager
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database writer."""

    db = MagicMock()
    db.save_category = AsyncMock()
    db.save_channel = AsyncMock()
    db.get_category = AsyncMock()
    db.get_category_by_name = AsyncMock()
    db.get_channel = AsyncMock()
    db.get_channel_by_name = AsyncMock()
    return db


@pytest.fixture
def mock_jsonl() -> MagicMock:
    """Mock JSONL writer."""

    jsonl = MagicMock()
    jsonl.write_category = AsyncMock()
    jsonl.write_channel = AsyncMock()
    return jsonl


@pytest.fixture
def category_manager(mock_db: MagicMock, mock_jsonl: MagicMock) -> CategoryManager:
    """Create CategoryManager for testing."""

    return CategoryManager(db=mock_db, jsonl=mock_jsonl, server_id=123456789)


@pytest.fixture
def channel_manager(mock_db: MagicMock, mock_jsonl: MagicMock) -> ChannelManager:
    """Create ChannelManager for testing."""

    return ChannelManager(db=mock_db, jsonl=mock_jsonl, server_id=123456789)


@pytest.mark.asyncio
async def test_save_category(category_manager: CategoryManager, mock_db: MagicMock, mock_jsonl: MagicMock) -> None:
    """save_category persists to both DB and JSONL."""

    category = DiscordCategory(id=1, name="Test", server_id=123456789)

    await category_manager.save_category(category)

    mock_db.save_category.assert_called_once_with(category)
    mock_jsonl.write_category.assert_called_once_with(category)


@pytest.mark.asyncio
async def test_discover_categories(category_manager: CategoryManager) -> None:
    """discover_categories finds and saves all categories."""

    class DummyCategory:
        def __init__(self, id_: int, name: str, position: int) -> None:
            self.id = id_
            self.name = name
            self.position = position

    mock_guild = MagicMock()
    mock_guild.channels = [
        DummyCategory(100, "Category1", 0),
        "not-a-category",
        DummyCategory(101, "Category2", 1),
    ]

    category_manager.save_category = AsyncMock()

    with patch("discordia.managers.category_manager.GuildCategory", DummyCategory):
        categories = await category_manager.discover_categories(mock_guild)

    assert [c.name for c in categories] == ["Category1", "Category2"]
    assert category_manager.save_category.call_count == 2


@pytest.mark.asyncio
async def test_get_category_by_id(category_manager: CategoryManager, mock_db: MagicMock) -> None:
    """get_category retrieves category by ID."""

    expected = DiscordCategory(id=1, name="Test", server_id=123456789)
    mock_db.get_category.return_value = expected

    result = await category_manager.get_category(1)

    assert result == expected
    mock_db.get_category.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_category_not_found(category_manager: CategoryManager, mock_db: MagicMock) -> None:
    """get_category raises error if not found."""

    mock_db.get_category.return_value = None

    with pytest.raises(CategoryNotFoundError):
        await category_manager.get_category(999)


@pytest.mark.asyncio
async def test_get_category_by_name(category_manager: CategoryManager, mock_db: MagicMock) -> None:
    """get_category_by_name retrieves by name."""

    expected = DiscordCategory(id=1, name="Test", server_id=123456789)
    mock_db.get_category_by_name.return_value = expected

    result = await category_manager.get_category_by_name("Test")

    assert result == expected
    mock_db.get_category_by_name.assert_called_once_with("Test", 123456789)


@pytest.mark.asyncio
async def test_get_category_by_name_not_found(category_manager: CategoryManager, mock_db: MagicMock) -> None:
    """get_category_by_name raises error if not found."""

    mock_db.get_category_by_name.return_value = None

    with pytest.raises(CategoryNotFoundError):
        await category_manager.get_category_by_name("Nonexistent")


@pytest.mark.asyncio
async def test_save_channel(channel_manager: ChannelManager, mock_db: MagicMock, mock_jsonl: MagicMock) -> None:
    """save_channel persists to DB and JSONL."""

    channel = DiscordTextChannel(id=1, name="test-channel", server_id=123456789)

    await channel_manager.save_channel(channel)

    mock_db.save_channel.assert_called_once_with(channel)
    mock_jsonl.write_channel.assert_called_once_with(channel)


@pytest.mark.asyncio
async def test_get_channel(channel_manager: ChannelManager, mock_db: MagicMock) -> None:
    """get_channel returns a stored channel."""

    expected = DiscordTextChannel(id=1, name="test", server_id=123456789)
    mock_db.get_channel.return_value = expected

    result = await channel_manager.get_channel(1)

    assert result == expected
    mock_db.get_channel.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_channel_not_found(channel_manager: ChannelManager, mock_db: MagicMock) -> None:
    """get_channel raises ChannelNotFoundError when channel is missing."""

    mock_db.get_channel.return_value = None

    with pytest.raises(ChannelNotFoundError):
        await channel_manager.get_channel(999)


def test_is_log_channel(channel_manager: ChannelManager) -> None:
    """is_log_channel validates YYYY-MM-DD pattern."""

    assert channel_manager.is_log_channel("2024-12-14") is True
    assert channel_manager.is_log_channel("2024-01-01") is True
    assert channel_manager.is_log_channel("general") is False
    assert channel_manager.is_log_channel("2024-1-1") is False
    assert channel_manager.is_log_channel("24-12-14") is False


def test_get_daily_channel_name(channel_manager: ChannelManager) -> None:
    """get_daily_channel_name returns a value in YYYY-MM-DD format."""

    name = channel_manager.get_daily_channel_name()
    assert channel_manager.is_log_channel(name) is True


@pytest.mark.asyncio
async def test_ensure_daily_log_channel_returns_existing(channel_manager: ChannelManager, mock_db: MagicMock) -> None:
    """ensure_daily_log_channel returns existing channel from database."""

    existing = DiscordTextChannel(
        id=1,
        name="2024-12-14",
        category_id=100,
        server_id=123456789,
    )
    mock_db.get_channel_by_name.return_value = existing

    mock_guild = MagicMock()
    mock_guild.create_text_channel = AsyncMock()

    with patch.object(channel_manager, "get_daily_channel_name", return_value="2024-12-14"):
        result = await channel_manager.ensure_daily_log_channel(mock_guild, 100)

    assert result == existing
    mock_guild.create_text_channel.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_daily_log_channel_creates_new(channel_manager: ChannelManager, mock_db: MagicMock) -> None:
    """ensure_daily_log_channel creates a new channel when missing."""

    mock_db.get_channel_by_name.return_value = None

    mock_guild = MagicMock()
    mock_discord_channel = MagicMock()
    mock_discord_channel.id = 200
    mock_discord_channel.name = "2024-12-14"
    mock_discord_channel.position = 0
    mock_guild.create_text_channel = AsyncMock(return_value=mock_discord_channel)

    with patch.object(channel_manager, "get_daily_channel_name", return_value="2024-12-14"):
        result = await channel_manager.ensure_daily_log_channel(mock_guild, 100)

    assert result.name == "2024-12-14"
    assert result.category_id == 100
    mock_guild.create_text_channel.assert_called_once()
