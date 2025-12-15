# src/discordia/templates/__init__.py
from __future__ import annotations

from discordia.templates.base import TemplateModel
from discordia.templates.category import CategoryTemplate
from discordia.templates.channel import (
    AnnouncementChannelTemplate,
    ChannelTemplate,
    ChannelType,
    ForumChannelTemplate,
    TextChannelTemplate,
    VoiceChannelTemplate,
)
from discordia.templates.patterns import ChannelPattern, DailyLogPattern, PrefixedPattern
from discordia.templates.server import ServerTemplate
from discordia.templates.weekday_pattern import WeekDayPattern

__all__ = [
    "AnnouncementChannelTemplate",
    "CategoryTemplate",
    "ChannelPattern",
    "ChannelTemplate",
    "ChannelType",
    "DailyLogPattern",
    "ForumChannelTemplate",
    "PrefixedPattern",
    "ServerTemplate",
    "TemplateModel",
    "TextChannelTemplate",
    "VoiceChannelTemplate",
    "WeekDayPattern",
]
