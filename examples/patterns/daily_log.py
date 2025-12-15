# examples/patterns/daily_log.py
from __future__ import annotations

from datetime import date, timedelta

from pydantic import Field

from discordia import ChannelPattern, ChannelTemplate, TextChannelTemplate


class DailyLogPattern(ChannelPattern):
    """Generates daily log channels in YYYY-MM-DD format."""

    days_ahead: int = Field(default=1, ge=0, le=30, description="Days to pre-generate ahead")
    days_behind: int = Field(default=7, ge=0, le=90, description="Days to keep behind")
    topic: str | None = Field(default="Daily conversation log", description="Topic for generated channels")

    def generate(self) -> list[ChannelTemplate]:
        """Generate channel templates for date range."""
        today = date.today()
        start = today - timedelta(days=self.days_behind)
        end = today + timedelta(days=self.days_ahead)

        channels: list[ChannelTemplate] = []
        current = start
        while current <= end:
            channels.append(
                TextChannelTemplate(
                    name=current.isoformat(),
                    topic=self.topic,
                    position=None,
                )
            )
            current += timedelta(days=1)
        return channels


__all__ = ["DailyLogPattern"]
