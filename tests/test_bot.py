# tests/test_bot.py
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.bot import Bot
from discordia.exceptions import CategoryNotFoundError
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
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
    assert bot.llm_client is not None
    assert bot.category_manager is not None
    assert bot.channel_manager is not None
    assert bot.message_handler is not None
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
async def test_ensure_daily_log_channel_creates_channel(bot: Bot) -> None:
    """_ensure_daily_log_channel creates today's channel."""

    bot.category_manager.get_category_by_name = AsyncMock(
        return_value=DiscordCategory(id=100, name="Log", server_id=bot.settings.server_id)
    )

    mock_guild = MagicMock()
    bot.client.fetch_guild = AsyncMock(return_value=mock_guild)

    mock_channel = DiscordTextChannel(
        id=200,
        name="2024-12-14",
        category_id=100,
        server_id=bot.settings.server_id,
    )
    bot.channel_manager.ensure_daily_log_channel = AsyncMock(return_value=mock_channel)

    await bot._ensure_daily_log_channel()

    bot.channel_manager.ensure_daily_log_channel.assert_called_once_with(mock_guild, 100)
    assert bot._last_date_checked == date.today()


@pytest.mark.asyncio
async def test_ensure_daily_log_channel_skips_if_already_checked(bot: Bot) -> None:
    """_ensure_daily_log_channel skips if already checked today."""

    bot._last_date_checked = date.today()
    bot.category_manager.get_category_by_name = AsyncMock()

    await bot._ensure_daily_log_channel()

    bot.category_manager.get_category_by_name.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_daily_log_channel_handles_missing_category(bot: Bot) -> None:
    """_ensure_daily_log_channel handles missing log category gracefully."""

    bot.category_manager.get_category_by_name = AsyncMock(side_effect=CategoryNotFoundError("Not found"))

    await bot._ensure_daily_log_channel()

    assert bot._last_date_checked is None


@pytest.mark.asyncio
async def test_on_ready_ensures_daily_channel(bot: Bot) -> None:
    """on_ready creates daily log channel when auto_create enabled."""

    bot.settings.auto_create_daily_logs = True

    bot.db.initialize = AsyncMock()

    mock_guild = MagicMock()
    bot.client.fetch_guild = AsyncMock(return_value=mock_guild)

    bot.category_manager.discover_categories = AsyncMock()
    bot.channel_manager.discover_channels = AsyncMock()
    bot._ensure_daily_log_channel = AsyncMock()

    mock_event = MagicMock()
    mock_event.user.username = "TestBot"
    mock_event.guilds = [MagicMock()]

    await bot._on_ready(mock_event)

    bot._ensure_daily_log_channel.assert_called_once()


@pytest.mark.asyncio
async def test_on_ready_skips_daily_channel_if_disabled(bot: Bot) -> None:
    """on_ready skips daily channel creation when disabled."""

    bot.settings.auto_create_daily_logs = False
    bot.db.initialize = AsyncMock()

    mock_guild = MagicMock()
    bot.client.fetch_guild = AsyncMock(return_value=mock_guild)

    bot.category_manager.discover_categories = AsyncMock()
    bot.channel_manager.discover_channels = AsyncMock()
    bot._ensure_daily_log_channel = AsyncMock()

    mock_event = MagicMock()
    mock_event.user.username = "TestBot"
    mock_event.guilds = [MagicMock()]

    await bot._on_ready(mock_event)

    bot._ensure_daily_log_channel.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_ignores_bot_messages(bot: Bot) -> None:
    """Message handler ignores bot messages."""

    mock_event = MagicMock()
    mock_event.message.author.bot = True

    bot._ensure_daily_log_channel = AsyncMock()
    bot.message_handler.handle_message = AsyncMock()

    await bot._on_message(mock_event)

    bot._ensure_daily_log_channel.assert_not_called()
    bot.message_handler.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_checks_daily_channel(bot: Bot) -> None:
    """on_message checks for daily channel before processing."""

    bot.settings.auto_create_daily_logs = True

    mock_event = MagicMock()
    mock_event.message.author.bot = False
    mock_event.message.id = 12345
    mock_event.message.author.username = "testuser"
    mock_event.message.channel.id = 67890

    bot._ensure_daily_log_channel = AsyncMock()
    bot.message_handler.handle_message = AsyncMock()

    await bot._on_message(mock_event)

    bot._ensure_daily_log_channel.assert_called_once()
    bot.message_handler.handle_message.assert_called_once_with(mock_event.message)


@pytest.mark.asyncio
async def test_stop_closes_database(bot: Bot) -> None:
    """Stop method closes database connection."""

    bot.db.close = AsyncMock()
    bot.client.stop = AsyncMock()

    await bot.stop()

    bot.db.close.assert_called_once()
    bot.client.stop.assert_called_once()
