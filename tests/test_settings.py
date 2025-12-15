# tests/test_settings.py
from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from discordia.settings import Settings


def test_settings_with_required_fields() -> None:
    """Settings can be created with all required fields."""
    settings = Settings(
        discord_token="test-token",
        server_id=123456789,
        anthropic_api_key="test-key",
    )

    assert settings.discord_token == "test-token"
    assert settings.server_id == 123456789
    assert settings.anthropic_api_key == "test-key"


def test_settings_with_defaults() -> None:
    """Optional fields use default values."""
    settings = Settings(
        discord_token="test-token",
        server_id=123456789,
        anthropic_api_key="test-key",
    )

    assert settings.log_category_name == "Log"
    assert settings.auto_create_daily_logs is True
    assert settings.database_url == "sqlite+aiosqlite:///discordia.db"
    assert settings.jsonl_path == "discordia_backup.jsonl"
    assert settings.llm_model == "claude-sonnet-4-20250514"
    assert settings.message_context_limit == 20
    assert settings.max_message_length == 2000


def test_settings_missing_required_field() -> None:
    """Settings raises ValidationError when required field missing."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            discord_token="test-token",
            server_id=123456789,
        )

    assert "anthropic_api_key" in str(exc_info.value)


def test_settings_invalid_server_id() -> None:
    """Settings validates server_id is positive."""
    with pytest.raises(ValidationError):
        Settings(
            discord_token="test-token",
            server_id=-1,
            anthropic_api_key="test-key",
        )


@pytest.mark.parametrize("value", [0, 101])
def test_settings_invalid_message_context_limit(value: int) -> None:
    """Settings validates message_context_limit is between 1 and 100."""
    with pytest.raises(ValidationError):
        Settings(
            discord_token="test-token",
            server_id=123456789,
            anthropic_api_key="test-key",
            message_context_limit=value,
        )


@pytest.mark.parametrize("value", [0, 2001])
def test_settings_invalid_max_message_length(value: int) -> None:
    """Settings validates max_message_length is between 1 and 2000."""
    with pytest.raises(ValidationError):
        Settings(
            discord_token="test-token",
            server_id=123456789,
            anthropic_api_key="test-key",
            max_message_length=value,
        )


def test_settings_override_defaults() -> None:
    """Optional fields can be overridden."""
    settings = Settings(
        discord_token="test-token",
        server_id=123456789,
        anthropic_api_key="test-key",
        log_category_name="Custom",
        message_context_limit=50,
        max_message_length=1500,
        auto_create_daily_logs=False,
    )

    assert settings.log_category_name == "Custom"
    assert settings.message_context_limit == 50
    assert settings.max_message_length == 1500
    assert settings.auto_create_daily_logs is False


def test_settings_environment_variable_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings loads required fields from environment variables."""
    for key in ("DISCORD_TOKEN", "SERVER_ID", "ANTHROPIC_API_KEY"):
        if key in os.environ:
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("DISCORD_TOKEN", "env-token")
    monkeypatch.setenv("SERVER_ID", "42")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    monkeypatch.setenv("LOG_CATEGORY_NAME", "EnvLog")

    settings = Settings()

    assert settings.discord_token == "env-token"
    assert settings.server_id == 42
    assert settings.anthropic_api_key == "env-key"
    assert settings.log_category_name == "EnvLog"


def test_settings_field_descriptions_present() -> None:
    """Fields provide descriptions for documentation and tooling."""
    fields = Settings.model_fields
    assert fields["discord_token"].description
    assert fields["server_id"].description
    assert fields["anthropic_api_key"].description
    assert fields["log_category_name"].description
