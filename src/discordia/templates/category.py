# src/discordia/templates/category.py
from __future__ import annotations

from pydantic import Field

from discordia.templates.base import TemplateModel
from discordia.templates.channel import ChannelTemplate
from discordia.types import CategoryName


class CategoryTemplate(TemplateModel):
    """Template for a Discord category containing channels."""

    name: CategoryName
    position: int | None = None
    channels: list[ChannelTemplate] = Field(default_factory=list)


__all__ = ["CategoryTemplate"]
