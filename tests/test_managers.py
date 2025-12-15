# tests/test_managers.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.exceptions import CategoryNotFoundError
from discordia.managers.category_manager import CategoryManager
from discordia.models.category import DiscordCategory


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database writer."""

    db = MagicMock()
    db.save_category = AsyncMock()
    db.get_category = AsyncMock()
    db.get_category_by_name = AsyncMock()
    return db


@pytest.fixture
def mock_jsonl() -> MagicMock:
    """Mock JSONL writer."""

    jsonl = MagicMock()
    jsonl.write_category = AsyncMock()
    return jsonl


@pytest.fixture
def category_manager(mock_db: MagicMock, mock_jsonl: MagicMock) -> CategoryManager:
    """Create CategoryManager for testing."""

    return CategoryManager(db=mock_db, jsonl=mock_jsonl, server_id=123456789)


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
