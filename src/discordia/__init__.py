# src/discordia/__init__.py
from __future__ import annotations

from discordia.engine import Bot
from discordia.exceptions import (
    CategoryNotFoundError,
    ChannelNotFoundError,
    ConfigurationError,
    ContextTooLargeError,
    DatabaseError,
    DiscordAPIError,
    DiscordiaError,
    HandlerError,
    JSONLError,
    LLMAPIError,
    LLMError,
    MessageSendError,
    PersistenceError,
    ReconciliationError,
    StateError,
    TemplateError,
)
from discordia.settings import Settings
from discordia.templates import (
    AnnouncementChannelTemplate,
    CategoryTemplate,
    ChannelPattern,
    ChannelTemplate,
    ChannelType,
    DailyLogPattern,
    ForumChannelTemplate,
    PrefixedPattern,
    ServerTemplate,
    TemplateModel,
    TextChannelTemplate,
    VoiceChannelTemplate,
    WeekDayPattern,
)

__version__ = "0.2.0"

__all__ = [
    "AnnouncementChannelTemplate",
    "Bot",
    "CategoryNotFoundError",
    "CategoryTemplate",
    "ChannelNotFoundError",
    "ChannelPattern",
    "ChannelTemplate",
    "ChannelType",
    "ConfigurationError",
    "ContextTooLargeError",
    "DailyLogPattern",
    "DatabaseError",
    "DiscordAPIError",
    "DiscordiaError",
    "ForumChannelTemplate",
    "HandlerError",
    "JSONLError",
    "LLMAPIError",
    "LLMError",
    "MessageSendError",
    "PersistenceError",
    "PrefixedPattern",
    "ReconciliationError",
    "ServerTemplate",
    "Settings",
    "StateError",
    "TemplateError",
    "TemplateModel",
    "TextChannelTemplate",
    "VoiceChannelTemplate",
    "WeekDayPattern",
]

