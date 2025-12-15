# src/discordia/templates/server.py
from __future__ import annotations

from pydantic import Field

from discordia.templates.base import TemplateModel
from discordia.templates.category import CategoryTemplate
from discordia.templates.channel import ChannelTemplate
from discordia.templates.patterns import ChannelPattern


class ServerTemplate(TemplateModel):
    """Complete declarative server structure."""

    categories: list[CategoryTemplate] = Field(default_factory=list)
    uncategorized_channels: list[ChannelTemplate] = Field(default_factory=list)
    patterns: list[ChannelPattern] = Field(default_factory=list)

    def resolve_patterns(self) -> ServerTemplate:
        """Expand patterns into concrete channel templates."""
        expanded_channels = list(self.uncategorized_channels)
        for pattern in self.patterns:
            expanded_channels.extend(pattern.generate())

        return ServerTemplate(
            categories=self.categories,
            uncategorized_channels=expanded_channels,
            patterns=[],
        )


__all__ = ["ServerTemplate"]
