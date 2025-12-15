# src/discordia/models/base.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DiscordiaModel(BaseModel):
    """Base model for Discordia entities.

    The reference implementation uses SQLModel for persistence, but Discordia
    keeps its core models usable without requiring any optional ORM/runtime
    dependencies to be installed.
    """

    model_config = ConfigDict(extra="ignore")


__all__ = ["DiscordiaModel"]
