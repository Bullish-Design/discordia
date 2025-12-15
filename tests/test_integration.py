# tests/test_integration.py
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discordia.bot import Bot
from discordia.models.category import DiscordCategory
from discordia.models.channel import DiscordTextChannel
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
    )


@pytest.mark.asyncio
async def test_full_message_flow(integration_settings: Settings) -> None:
    """Test that the bot's ready flow wires up daily log channel checks."""

    with patch("discordia.bot.Client"):
        bot = Bot(integration_settings)

        bot.db.initialize = AsyncMock()
        bot.category_manager.discover_categories = AsyncMock()
        bot.channel_manager.discover_channels = AsyncMock()

        mock_guild = MagicMock()
        mock_guild.channels = []
        bot.client.fetch_guild = AsyncMock(return_value=mock_guild)

        mock_category = DiscordCategory(
            id=100,
            name="Log",
            server_id=integration_settings.server_id,
        )
        bot.category_manager.get_category_by_name = AsyncMock(return_value=mock_category)

        today_channel = DiscordTextChannel(
            id=200,
            name=date.today().isoformat(),
            category_id=100,
            server_id=integration_settings.server_id,
        )
        bot.channel_manager.ensure_daily_log_channel = AsyncMock(return_value=today_channel)

        mock_ready = MagicMock()
        mock_ready.user.username = "TestBot"
        mock_ready.guilds = [MagicMock()]

        await bot._on_ready(mock_ready)

        bot.db.initialize.assert_called_once()
        bot.category_manager.discover_categories.assert_called_once()
        bot.channel_manager.discover_channels.assert_called_once()
        bot.channel_manager.ensure_daily_log_channel.assert_called_once()
        assert bot._last_date_checked == date.today()


@pytest.mark.asyncio
async def test_date_change_creates_new_channel(integration_settings: Settings) -> None:
    """Test that a new day triggers a new daily channel check."""

    with patch("discordia.bot.Client"):
        bot = Bot(integration_settings)
        bot._last_date_checked = date.today() - timedelta(days=1)

        mock_category = DiscordCategory(
            id=100,
            name="Log",
            server_id=integration_settings.server_id,
        )
        bot.category_manager.get_category_by_name = AsyncMock(return_value=mock_category)

        mock_guild = MagicMock()
        bot.client.fetch_guild = AsyncMock(return_value=mock_guild)

        bot.channel_manager.ensure_daily_log_channel = AsyncMock(
            return_value=DiscordTextChannel(
                id=200,
                name=date.today().isoformat(),
                category_id=100,
                server_id=integration_settings.server_id,
            )
        )

        await bot._ensure_daily_log_channel()

        bot.channel_manager.ensure_daily_log_channel.assert_called_once_with(mock_guild, 100)
        assert bot._last_date_checked == date.today()
