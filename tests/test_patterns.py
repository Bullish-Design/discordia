# tests/test_patterns.py
from __future__ import annotations

from datetime import date, timedelta

from discordia.templates.channel import TextChannelTemplate
from discordia.templates.patterns import DailyLogPattern, PrefixedPattern


def test_daily_log_pattern_default():
    """DailyLogPattern generates channels for date range."""
    pattern = DailyLogPattern()
    channels = pattern.generate()

    assert len(channels) > 0
    assert all(isinstance(ch, TextChannelTemplate) for ch in channels)


def test_daily_log_pattern_range():
    """DailyLogPattern respects days_ahead and days_behind."""
    pattern = DailyLogPattern(days_ahead=2, days_behind=3)
    channels = pattern.generate()

    expected_count = 2 + 3 + 1  # ahead + behind + today
    assert len(channels) == expected_count


def test_daily_log_pattern_channel_names():
    """DailyLogPattern generates ISO date channel names."""
    pattern = DailyLogPattern(days_ahead=0, days_behind=0)
    channels = pattern.generate()

    today = date.today()
    assert len(channels) == 1
    assert channels[0].name == today.isoformat()


def test_daily_log_pattern_with_topic():
    """DailyLogPattern applies topic to generated channels."""
    pattern = DailyLogPattern(days_ahead=1, days_behind=1, topic="Daily log")
    channels = pattern.generate()

    assert all(ch.topic == "Daily log" for ch in channels)


def test_daily_log_pattern_ordering():
    """DailyLogPattern generates channels in chronological order."""
    pattern = DailyLogPattern(days_ahead=2, days_behind=2)
    channels = pattern.generate()

    today = date.today()
    start_date = today - timedelta(days=2)

    for i, channel in enumerate(channels):
        expected_date = start_date + timedelta(days=i)
        assert channel.name == expected_date.isoformat()


def test_prefixed_pattern_basic():
    """PrefixedPattern generates prefixed channels."""
    pattern = PrefixedPattern(
        prefix="team",
        suffixes=["alpha", "beta", "gamma"],
    )
    channels = pattern.generate()

    assert len(channels) == 3
    assert channels[0].name == "team-alpha"
    assert channels[1].name == "team-beta"
    assert channels[2].name == "team-gamma"


def test_prefixed_pattern_custom_separator():
    """PrefixedPattern uses custom separator."""
    pattern = PrefixedPattern(
        prefix="category",
        suffixes=["one", "two"],
        #separator="-",
    )
    channels = pattern.generate()

    assert channels[0].name == "category-one"
    assert channels[1].name == "category-two"


def test_prefixed_pattern_with_positions():
    """PrefixedPattern assigns sequential positions."""
    pattern = PrefixedPattern(
        prefix="channel",
        suffixes=["a", "b", "c"],
    )
    channels = pattern.generate()

    assert channels[0].position == 0
    assert channels[1].position == 1
    assert channels[2].position == 2


def test_prefixed_pattern_without_topic():
    """PrefixedPattern generates channels without topics by default."""
    pattern = PrefixedPattern(
        prefix="test",
        suffixes=["one"],
    )
    channels = pattern.generate()

    assert channels[0].topic is None


def test_prefixed_pattern_with_topic_generator():
    """PrefixedPattern can use topic generator function."""

    def topic_gen(suffix: str) -> str:
        return f"Topic for {suffix}"

    pattern = PrefixedPattern(
        prefix="test",
        suffixes=["alpha", "beta"],
        topic_generator=topic_gen,
    )
    channels = pattern.generate()

    assert channels[0].topic == "Topic for alpha"
    assert channels[1].topic == "Topic for beta"


def test_prefixed_pattern_empty_suffixes():
    """PrefixedPattern handles empty suffix list."""
    pattern = PrefixedPattern(prefix="test", suffixes=[])
    channels = pattern.generate()
    assert channels == []
