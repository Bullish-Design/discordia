# tests/test_server_template.py
from __future__ import annotations

from discordia.templates.category import CategoryTemplate
from discordia.templates.channel import TextChannelTemplate
from discordia.templates.patterns import DailyLogPattern, PrefixedPattern
from discordia.templates.server import ServerTemplate


def test_server_template_resolve_patterns_empty():
    """ServerTemplate with no patterns returns self."""
    server = ServerTemplate(
        categories=[],
        uncategorized_channels=[
            TextChannelTemplate(name="general"),
        ],
    )
    resolved = server.resolve_patterns()

    assert len(resolved.uncategorized_channels) == 1
    assert len(resolved.patterns) == 0


def test_server_template_resolve_daily_log():
    """ServerTemplate resolves DailyLogPattern."""
    pattern = DailyLogPattern(days_ahead=1, days_behind=1)
    server = ServerTemplate(patterns=[pattern])

    resolved = server.resolve_patterns()

    assert len(resolved.uncategorized_channels) == 3  # yesterday, today, tomorrow
    assert len(resolved.patterns) == 0


def test_server_template_resolve_prefixed():
    """ServerTemplate resolves PrefixedPattern."""
    pattern = PrefixedPattern(
        prefix="team",
        suffixes=["alpha", "beta"],
    )
    server = ServerTemplate(patterns=[pattern])

    resolved = server.resolve_patterns()

    assert len(resolved.uncategorized_channels) == 2
    assert resolved.uncategorized_channels[0].name == "team-alpha"
    assert resolved.uncategorized_channels[1].name == "team-beta"


def test_server_template_resolve_multiple_patterns():
    """ServerTemplate resolves multiple patterns."""
    pattern1 = PrefixedPattern(prefix="group", suffixes=["a", "b"])
    pattern2 = PrefixedPattern(prefix="team", suffixes=["x"])

    server = ServerTemplate(patterns=[pattern1, pattern2])
    resolved = server.resolve_patterns()

    assert len(resolved.uncategorized_channels) == 3
    assert resolved.uncategorized_channels[0].name == "group-a"
    assert resolved.uncategorized_channels[1].name == "group-b"
    assert resolved.uncategorized_channels[2].name == "team-x"


def test_server_template_resolve_preserves_static():
    """ServerTemplate preserves static channels during resolution."""
    server = ServerTemplate(
        uncategorized_channels=[
            TextChannelTemplate(name="static-channel"),
        ],
        patterns=[
            PrefixedPattern(prefix="dynamic", suffixes=["one"]),
        ],
    )

    resolved = server.resolve_patterns()

    assert len(resolved.uncategorized_channels) == 2
    assert resolved.uncategorized_channels[0].name == "static-channel"
    assert resolved.uncategorized_channels[1].name == "dynamic-one"


def test_server_template_resolve_preserves_categories():
    """ServerTemplate preserves categories during resolution."""
    category = CategoryTemplate(
        name="Test Category",
        channels=[TextChannelTemplate(name="test")],
    )
    server = ServerTemplate(
        categories=[category],
        patterns=[PrefixedPattern(prefix="x", suffixes=["y"])],
    )

    resolved = server.resolve_patterns()

    assert len(resolved.categories) == 1
    assert resolved.categories[0].name == "Test Category"
