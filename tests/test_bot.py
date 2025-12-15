# tests/test_bot.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.bot import Bot
from discordia.settings import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""

    return Settings(
        discord_token="test-token",
        server_id=123456789,
        anthropic_api_key="test-key",
    )


@pytest.fixture
def bot(mock_settings: Settings) -> Bot:
    """Create bot instance for testing."""

    with patch("discordia.bot.Client"):
        return Bot(mock_settings)


def test_bot_initialization(mock_settings: Settings) -> None:
    """Bot initializes with settings."""

    with patch("discordia.bot.Client"):
        bot = Bot(mock_settings)

    assert bot.settings == mock_settings
    assert bot.db is not None
    assert bot.jsonl is not None
    assert bot.category_manager is not None
    assert bot.client is not None


def test_bot_creates_database_writer(mock_settings: Settings) -> None:
    """Bot creates database writer with correct URL."""

    with patch("discordia.bot.Client"):
        bot = Bot(mock_settings)

    assert bot.db.database_url == mock_settings.database_url


def test_bot_creates_jsonl_writer(mock_settings: Settings) -> None:
    """Bot creates JSONL writer with correct path."""

    with patch("discordia.bot.Client"):
        bot = Bot(mock_settings)

    assert bot.jsonl.filepath == mock_settings.jsonl_path


def test_bot_sets_up_listeners(mock_settings: Settings) -> None:
    """Bot registers event listeners."""

    with patch("discordia.bot.Client") as mock_client:
        _ = Bot(mock_settings)

    assert mock_client.return_value.add_listener.called


@pytest.mark.asyncio
async def test_on_ready_initializes_database(bot: Bot) -> None:
    """Ready event initializes database."""

    bot.db.initialize = AsyncMock()
    bot.client.fetch_guild = AsyncMock(return_value=MagicMock())
    bot.category_manager.discover_categories = AsyncMock()

    mock_event = MagicMock()
    mock_event.user.username = "TestBot"
    mock_event.guilds = [MagicMock()]

    await bot._on_ready(mock_event)

    bot.db.initialize.assert_called_once()
    bot.client.fetch_guild.assert_called_once_with(bot.settings.server_id)
    bot.category_manager.discover_categories.assert_called_once()


@pytest.mark.asyncio
async def test_on_message_ignores_bot_messages(bot: Bot) -> None:
    """Message handler ignores bot messages."""

    mock_event = MagicMock()
    mock_event.message.author.bot = True

    await bot._on_message(mock_event)


@pytest.mark.asyncio
async def test_on_message_processes_user_messages(bot: Bot) -> None:
    """Message handler processes user messages."""

    mock_event = MagicMock()
    mock_event.message.author.bot = False
    mock_event.message.id = 12345
    mock_event.message.author.username = "testuser"
    mock_event.message.channel.id = 67890

    await bot._on_message(mock_event)


@pytest.mark.asyncio
async def test_stop_closes_database(bot: Bot) -> None:
    """Stop method closes database connection."""

    bot.db.close = AsyncMock()
    bot.client.stop = AsyncMock()

    await bot.stop()

    bot.db.close.assert_called_once()
    bot.client.stop.assert_called_once()
