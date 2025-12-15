# src/discordia/templates/weekday_pattern.py
from __future__ import annotations

from datetime import date, timedelta

from pydantic import Field

from discordia.templates.base import TemplateModel
from discordia.templates.channel import ChannelTemplate, TextChannelTemplate
from discordia.templates.patterns import ChannelPattern


class WeekDayPattern(ChannelPattern):
    """Generates channels in WW-DD format (ISO week, day 01-07 with Monday as 01)."""

    weeks_ahead: int = Field(default=0, ge=0, le=4, description="Weeks to pre-generate ahead")
    weeks_behind: int = Field(default=1, ge=0, le=8, description="Weeks to keep behind")
    topic: str | None = Field(default="Weekly log channel", description="Topic for generated channels")

    def generate(self) -> list[ChannelTemplate]:
        """Generate channel templates for week-day range."""
        today = date.today()
        
        # Calculate date range
        days_behind = self.weeks_behind * 7 + today.weekday()
        days_ahead = self.weeks_ahead * 7 + (6 - today.weekday())
        
        start = today - timedelta(days=days_behind)
        end = today + timedelta(days=days_ahead)

        channels: list[ChannelTemplate] = []
        current = start
        while current <= end:
            iso_cal = current.isocalendar()
            week_num = iso_cal.week
            day_num = iso_cal.weekday  # Monday=1, Sunday=7
            
            name = f"{week_num:02d}-{day_num:02d}"
            
            channels.append(
                TextChannelTemplate(
                    name=name,
                    topic=self.topic,
                    position=None,
                )
            )
            current += timedelta(days=1)
        
        return channels


__all__ = ["WeekDayPattern"]
