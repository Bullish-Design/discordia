# tests/test_config.py
from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from discordia.config import BotConfig


def test_bot_config_valid() -> None:
    config = BotConfig(discord_token=SecretStr("test_token"), server_id=123456789)
    assert config.server_id == 123456789
    assert config.message_context_limit == 20


def test_bot_config_custom_limit() -> None:
    config = BotConfig(
        discord_token=SecretStr("test_token"),
        server_id=123456789,
        message_context_limit=50,
    )
    assert config.message_context_limit == 50


def test_bot_config_invalid_limit_low() -> None:
    with pytest.raises(ValidationError):
        BotConfig(
            discord_token=SecretStr("test_token"),
            server_id=123456789,
            message_context_limit=0,
        )


def test_bot_config_invalid_limit_high() -> None:
    with pytest.raises(ValidationError):
        BotConfig(
            discord_token=SecretStr("test_token"),
            server_id=123456789,
            message_context_limit=101,
        )


def test_bot_config_invalid_server_id() -> None:
    with pytest.raises(ValidationError):
        BotConfig(discord_token=SecretStr("test_token"), server_id=-1)


def test_bot_config_frozen() -> None:
    config = BotConfig(discord_token=SecretStr("test_token"), server_id=123456789)
    with pytest.raises(ValidationError):
        config.server_id = 999  # type: ignore[misc]
