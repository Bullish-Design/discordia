# src/discordia/__init__.py
from __future__ import annotations

"""Discordia - Discord bot framework."""

from discordia.bot import Bot
from discordia.config import BotConfig
from discordia.context import MessageContext
from discordia.discovery import DiscoveryEngine
from discordia.exceptions import (
    ConfigurationError,
    DiscordAPIError,
    DiscordiaError,
    EntityNotFoundError,
    StateError,
    ValidationError,
)
from discordia.handlers import EchoConfig, EchoHandler, Handler, LoggingConfig, LoggingHandler
from discordia.plugins import Plugin
from discordia.registry import EntityRegistry
from discordia.state import Category, Channel, MemoryState, Message, StateEntity, StateStore, User
from discordia.types import ChannelName, DiscordID, DiscordToken, MessageContent, Username

__version__ = "0.5.0"

__all__ = [
    "Bot",
    "DiscordiaError",
    "ConfigurationError",
    "StateError",
    "DiscordAPIError",
    "EntityNotFoundError",
    "ValidationError",
    "MessageContext",
    "BotConfig",
    "DiscoveryEngine",
    "EntityRegistry",
    "Plugin",
    "Handler",
    "LoggingHandler",
    "LoggingConfig",
    "EchoHandler",
    "EchoConfig",
    "DiscordID",
    "ChannelName",
    "Username",
    "MessageContent",
    "DiscordToken",
    "StateEntity",
    "Category",
    "Channel",
    "User",
    "Message",
    "StateStore",
    "MemoryState",
]
