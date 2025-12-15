# tests/test_settings.py
from __future__ import annotations

import pytest
from pydantic import ValidationError

from discordia.settings import Settings


def test_settings_required_fields():
    """Settings requires discord_token and server_id."""
    with pytest.raises(ValidationError):
        Settings()


def test_settings_minimal_config():
    """Settings can be created with minimal required fields."""
    settings = Settings(
        discord_token="test_token",
        server_id=123456789012345678,
        _env_file=None,
    )
    assert settings.discord_token.get_secret_value() == "test_token"
    assert settings.server_id == 123456789012345678


def test_settings_defaults():
    """Settings uses sensible defaults for optional fields."""
    settings = Settings(
        discord_token="test_token",
        server_id=123456789012345678,
        _env_file=None,
    )
    assert settings.auto_reconcile is True
    assert settings.reconcile_interval == 300
    assert settings.message_context_limit == 20
    assert settings.max_message_length == 2000
    assert settings.persistence_enabled is True
    assert settings.jsonl_path == "discordia_state.jsonl"
    assert settings.llm_provider == "anthropic"
    assert settings.llm_model == "claude-sonnet-4-20250514"
    assert settings.llm_temperature == 0.7


def test_settings_with_anthropic_key():
    """Settings accepts optional anthropic_api_key."""
    settings = Settings(
        discord_token="test_token",
        server_id=123456789012345678,
        anthropic_api_key="sk-ant-test",
        _env_file=None,
    )
    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "sk-ant-test"


def test_message_context_limit_validation():
    """message_context_limit must be between 1 and 100."""
    with pytest.raises(ValidationError, match="must be between 1 and 100"):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            message_context_limit=0,
            _env_file=None,
        )

    with pytest.raises(ValidationError, match="must be between 1 and 100"):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            message_context_limit=101,
            _env_file=None,
        )


def test_max_message_length_validation():
    """max_message_length must be between 1 and 2000."""
    with pytest.raises(ValidationError, match="must be between 1 and 2000"):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            max_message_length=0,
            _env_file=None,
        )

    with pytest.raises(ValidationError, match="must be between 1 and 2000"):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            max_message_length=2001,
            _env_file=None,
        )


def test_reconcile_interval_validation():
    """reconcile_interval must be non-negative."""
    with pytest.raises(ValidationError, match="must be non-negative"):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            reconcile_interval=-1,
            _env_file=None,
        )

    # Zero is valid (disables periodic reconciliation)
    settings = Settings(
        discord_token="test_token",
        server_id=123456789012345678,
        reconcile_interval=0,
        _env_file=None,
    )
    assert settings.reconcile_interval == 0


def test_llm_temperature_validation():
    """llm_temperature must be between 0.0 and 2.0."""
    with pytest.raises(ValidationError):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            llm_temperature=-0.1,
            _env_file=None,
        )

    with pytest.raises(ValidationError):
        Settings(
            discord_token="test_token",
            server_id=123456789012345678,
            llm_temperature=2.1,
            _env_file=None,
        )

    # Boundaries are valid
    settings = Settings(
        discord_token="test_token",
        server_id=123456789012345678,
        llm_temperature=0.0,
        _env_file=None,
    )
    assert settings.llm_temperature == 0.0

    settings = Settings(
        discord_token="test_token",
        server_id=123456789012345678,
        llm_temperature=2.0,
        _env_file=None,
    )
    assert settings.llm_temperature == 2.0
