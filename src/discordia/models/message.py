# src/discordia/models/message.py
from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, field_validator
from sqlmodel import Field

from discordia.models.base import ValidatedSQLModel


class DiscordMessage(ValidatedSQLModel, table=True):
    """Represents a Discord message.

    Messages are posted by users in channels and may be edited after creation.
    """

    model_config = ConfigDict(extra="ignore")

    __tablename__ = "messages"

    id: int = Field(primary_key=True, description="Discord message ID")
    content: str = Field(max_length=2000, description="Message content")
    author_id: int = Field(
        foreign_key="users.id",
        index=True,
        description="ID of the user who sent the message",
    )
    channel_id: int = Field(
        foreign_key="text_channels.id",
        index=True,
        description="ID of the channel containing the message",
    )
    timestamp: datetime = Field(index=True, description="When the message was sent")
    edited_at: datetime | None = Field(default=None, description="When the message was last edited")

    @field_validator("id", "author_id", "channel_id")
    @classmethod
    def _validate_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be a positive integer")
        return value

    @field_validator("content")
    @classmethod
    def _validate_content_not_none(cls, value: str) -> str:
        # Discord allows empty content (e.g., attachments), but for an LLM-oriented framework
        # we still want this to be a string.
        return value or ""

    def to_discord_format(self) -> dict[str, object]:
        """Convert to Discord API format.

        Timestamps are returned as ISO-8601 strings.
        """
        data: dict[str, object] = {
            "id": self.id,
            "content": self.content,
            "author_id": self.author_id,
            "channel_id": self.channel_id,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.edited_at is not None:
            data["edited_timestamp"] = self.edited_at.isoformat()
        else:
            data["edited_timestamp"] = None
        return data
