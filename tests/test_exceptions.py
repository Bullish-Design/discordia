# tests/test_exceptions.py
from __future__ import annotations

from discordia.exceptions import ConfigurationError, DiscordiaError, StateError


def test_base_exception() -> None:
    err = DiscordiaError("test error")
    assert str(err) == "test error"
    assert err.message == "test error"
    assert err.cause is None


def test_exception_with_cause() -> None:
    cause = ValueError("original error")
    err = DiscordiaError("wrapper error", cause=cause)
    assert "caused by" in str(err)
    assert err.cause is cause


def test_exception_hierarchy() -> None:
    assert issubclass(ConfigurationError, DiscordiaError)
    assert issubclass(StateError, DiscordiaError)


def test_exception_raising() -> None:
    try:
        raise ConfigurationError("bad config")
    except DiscordiaError as e:
        assert e.message == "bad config"
