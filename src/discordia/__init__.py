# src/discordia/__init__.py
from __future__ import annotations

from discordia.engine import Bot, MessageContext
from discordia.exceptions import (
    CategoryNotFoundError,
    ChannelNotFoundError,
    ConfigurationError,
    DiscordAPIError,
    DiscordiaError,
    HandlerError,
    MessageSendError,
    ReconciliationError,
    StateError,
    TemplateError,
)
from discordia.handlers import HandlerRouter, LoggingHandler, MessageHandler
from discordia.settings import Settings
from discordia.state import Category, Channel, EntityRegistry, MemoryState, Message, StateStore, User
from discordia.templates import (
    AnnouncementChannelTemplate,
    CategoryTemplate,
    ChannelPattern,
    ChannelTemplate,
    ChannelType,
    ForumChannelTemplate,
    ServerTemplate,
    TemplateModel,
    TextChannelTemplate,
    VoiceChannelTemplate,
)

__version__ = "0.3.0"

__all__ = [
    # Engine
    "Bot",
    "MessageContext",
    # Handlers
    "HandlerRouter",
    "LoggingHandler",
    "MessageHandler",
    # Settings
    "Settings",
    # State
    "Category",
    "Channel",
    "EntityRegistry",
    "MemoryState",
    "Message",
    "StateStore",
    "User",
    # Templates
    "AnnouncementChannelTemplate",
    "CategoryTemplate",
    "ChannelPattern",
    "ChannelTemplate",
    "ChannelType",
    "ForumChannelTemplate",
    "ServerTemplate",
    "TemplateModel",
    "TextChannelTemplate",
    "VoiceChannelTemplate",
    # Exceptions
    "CategoryNotFoundError",
    "ChannelNotFoundError",
    "ConfigurationError",
    "DiscordAPIError",
    "DiscordiaError",
    "HandlerError",
    "MessageSendError",
    "ReconciliationError",
    "StateError",
    "TemplateError",
]
