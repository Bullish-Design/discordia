# tests/test_integration.py
from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.bot import Bot
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
from discordia.models.message import DiscordMessage
from discordia.settings import Settings


@pytest.fixture
def integration_settings() -> Settings:
    """Settings for integration tests."""

    return Settings(
        discord_token="test-token",
        server_id=123456789,
        anthropic_api_key="test-key",
        log_category_name="Log",
        auto_create_daily_logs=True,
        message_context_limit=20,
        max_message_length=2000,
    )


async def _setup_bot_mocks(bot: Bot) -> None:
    """Setup Bot dependencies with async-safe mocks."""

    bot.db.initialize = AsyncMock()
    bot.db.save_user = AsyncMock()
    bot.db.save_message = AsyncMock()
    bot.db.save_category = AsyncMock()
    bot.db.save_channel = AsyncMock()
    bot.db.get_messages = AsyncMock(return_value=[])

    bot.jsonl.write_user = AsyncMock()
    bot.jsonl.write_message = AsyncMock()
    bot.jsonl.write_category = AsyncMock()
    bot.jsonl.write_channel = AsyncMock()

    bot.category_manager.discover_categories = AsyncMock()
    bot.channel_manager.discover_channels = AsyncMock()

    mock_category = DiscordCategory(id=100, name="Log", server_id=bot.settings.server_id)
    bot.category_manager.get_category_by_name = AsyncMock(return_value=mock_category)

    mock_channel = DiscordTextChannel(
        id=200,
        name=date.today().isoformat(),
        category_id=100,
        server_id=bot.settings.server_id,
    )
    bot.channel_manager.ensure_daily_log_channel = AsyncMock(return_value=mock_channel)
    bot.channel_manager.is_log_channel = MagicMock(return_value=True)

    bot.llm_client.generate_response = AsyncMock(return_value="Test response from Claude")

    mock_guild = MagicMock()
    mock_guild.channels = []
    bot.client.fetch_guild = AsyncMock(return_value=mock_guild)


def _create_mock_ready_event() -> MagicMock:
    mock_ready = MagicMock()
    mock_ready.user.username = "DiscordiaBot"
    mock_ready.guilds = [MagicMock()]
    return mock_ready


def _create_mock_message() -> MagicMock:
    """Create a Discord message-like mock compatible with MessageHandler."""

    mock_message = MagicMock()
    mock_message.id = 1000
    mock_message.content = "Hello bot!"
    mock_message.author.id = 2000
    mock_message.author.username = "testuser"
    mock_message.author.bot = False
    mock_message.channel.id = 3000
    mock_message.timestamp = datetime.utcnow()
    mock_message.edited_timestamp = None

    mock_channel = MagicMock()
    mock_channel.name = date.today().isoformat()
    mock_message.channel.fetch = AsyncMock(return_value=mock_channel)

    mock_reply = MagicMock()
    mock_reply.id = 4000
    mock_reply.author.id = 5000
    mock_reply.timestamp = datetime.utcnow()
    mock_reply.edited_timestamp = None
    mock_message.reply = AsyncMock(return_value=mock_reply)

    return mock_message


@pytest.mark.asyncio
async def test_complete_bot_lifecycle(integration_settings: Settings) -> None:
    """Test the complete bot lifecycle from startup through message handling."""

    with patch("discordia.bot.Client"):
        bot = Bot(integration_settings)
        await _setup_bot_mocks(bot)

        # Ensure context exists so MessageHandler proceeds to LLM.
        bot.db.get_messages = AsyncMock(
            return_value=[
                DiscordMessage(
                    id=1,
                    content="Previous message",
                    author_id=2000,
                    channel_id=3000,
                    timestamp=datetime.utcnow(),
                )
            ]
        )

        # 1) Startup
        await bot._on_ready(_create_mock_ready_event())

        bot.db.initialize.assert_called_once()
        bot.category_manager.discover_categories.assert_called_once()
        bot.channel_manager.discover_channels.assert_called_once()
        bot.channel_manager.ensure_daily_log_channel.assert_called_once()
        assert bot._last_date_checked == date.today()

        # 2) Message handling
        mock_message_event = MagicMock()
        mock_message_event.message = _create_mock_message()

        await bot._on_message(mock_message_event)

        # Message persisted (user + bot response)
        assert bot.db.save_user.called
        assert bot.db.save_message.call_count >= 2

        # LLM invoked
        bot.llm_client.generate_response.assert_called_once()

        # Response sent
        mock_message_event.message.reply.assert_called()


@pytest.mark.asyncio
async def test_date_change_creates_new_channel(integration_settings: Settings) -> None:
    """Test that a new day triggers a daily channel check."""

    with patch("discordia.bot.Client"):
        bot = Bot(integration_settings)
        await _setup_bot_mocks(bot)

        bot._last_date_checked = date.today() - timedelta(days=1)

        await bot._ensure_daily_log_channel()

        # Should re-run ensure, then update last checked.
        bot.channel_manager.ensure_daily_log_channel.assert_called_once()
        assert bot._last_date_checked == date.today()
