# src/discordia/templates/patterns.py
from __future__ import annotations

from abc import ABC, abstractmethod

from discordia.templates.base import TemplateModel
from discordia.templates.channel import ChannelTemplate


class ChannelPattern(TemplateModel, ABC):
    """Abstract base for dynamic channel generators.
    
    Subclass this to create patterns that dynamically generate
    channel templates based on custom logic (dates, prefixes, etc).
    """

    @abstractmethod
    def generate(self) -> list[ChannelTemplate]:
        """Generate channel templates based on pattern logic."""


__all__ = ["ChannelPattern"]
