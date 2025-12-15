# src/discordia/templates/patterns.py
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Callable

from pydantic import Field

from discordia.templates.base import TemplateModel
from discordia.templates.channel import ChannelTemplate, TextChannelTemplate


class ChannelPattern(TemplateModel, ABC):
    """Abstract base for dynamic channel generators."""

    @abstractmethod
    def generate(self) -> list[ChannelTemplate]:
        """Generate channel templates based on pattern logic."""


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


class PrefixedPattern(ChannelPattern):
    """Generates channels from a list with a common prefix."""

    prefix: str = Field(description="Prefix for all channel names")
    suffixes: list[str] = Field(description="Suffixes to append after prefix")
    separator: str = Field(default="-", description="Separator between prefix and suffix")
    topic_generator: Callable[[str], str] | None = Field(
        default=None, description="Optional function to generate topics"
    )

    def generate(self) -> list[ChannelTemplate]:
        """Generate prefixed channels."""
        channels: list[ChannelTemplate] = []
        for i, suffix in enumerate(self.suffixes):
            name = f"{self.prefix}{self.separator}{suffix}"
            topic = self.topic_generator(suffix) if self.topic_generator else None
            channels.append(
                TextChannelTemplate(
                    name=name,
                    topic=topic,
                    position=i,
                )
            )
        return channels


__all__ = ["ChannelPattern", "DailyLogPattern", "PrefixedPattern"]
