# examples/patterns/prefixed.py
from __future__ import annotations

from typing import Callable

from pydantic import Field

from discordia import ChannelPattern, ChannelTemplate, TextChannelTemplate


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


__all__ = ["PrefixedPattern"]
