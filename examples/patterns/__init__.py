# examples/patterns/__init__.py
from __future__ import annotations

from examples.patterns.daily_log import DailyLogPattern
from examples.patterns.prefixed import PrefixedPattern
from examples.patterns.weekday import WeekDayPattern

__all__ = ["DailyLogPattern", "PrefixedPattern", "WeekDayPattern"]
