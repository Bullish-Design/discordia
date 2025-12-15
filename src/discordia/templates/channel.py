# src/discordia/templates/channel.py
from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import Field

from discordia.templates.base import TemplateModel
from discordia.types import ChannelName


class ChannelType(StrEnum):
    """Discord channel types."""

    TEXT = "text"
    VOICE = "voice"
    FORUM = "forum"
    ANNOUNCEMENT = "announcement"


class BaseChannelTemplate(TemplateModel):
    """Base for all channel templates."""

    name: ChannelName
    topic: str | None = Field(default=None, max_length=1024)
    position: int | None = None


class TextChannelTemplate(BaseChannelTemplate):
    """Standard text channel."""

    type: Literal[ChannelType.TEXT] = ChannelType.TEXT
    slowmode_seconds: int = Field(default=0, ge=0, le=21600)
    nsfw: bool = False


class VoiceChannelTemplate(BaseChannelTemplate):
    """Voice channel."""

    type: Literal[ChannelType.VOICE] = ChannelType.VOICE
    bitrate: int = Field(default=64000, ge=8000, le=384000)
    user_limit: int = Field(default=0, ge=0, le=99)


class ForumChannelTemplate(BaseChannelTemplate):
    """Forum channel for threaded discussions."""

    type: Literal[ChannelType.FORUM] = ChannelType.FORUM
    default_thread_slowmode: int = Field(default=0, ge=0, le=21600)


class AnnouncementChannelTemplate(BaseChannelTemplate):
    """Announcement channel that can be followed."""

    type: Literal[ChannelType.ANNOUNCEMENT] = ChannelType.ANNOUNCEMENT


# Discriminated union - Pydantic auto-detects type from "type" field
ChannelTemplate = Annotated[
    Union[
        TextChannelTemplate,
        VoiceChannelTemplate,
        ForumChannelTemplate,
        AnnouncementChannelTemplate,
    ],
    Field(discriminator="type"),
]


__all__ = [
    "ChannelType",
    "BaseChannelTemplate",
    "TextChannelTemplate",
    "VoiceChannelTemplate",
    "ForumChannelTemplate",
    "AnnouncementChannelTemplate",
    "ChannelTemplate",
]
