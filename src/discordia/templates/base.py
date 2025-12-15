# src/discordia/templates/base.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TemplateModel(BaseModel):
    """Base class for declarative template models.

    Templates define desired state. They are:
    - Immutable after creation (frozen)
    - Validated strictly (forbid extra fields)
    - Serializable to JSON/YAML for storage
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        use_enum_values=True,
        validate_default=True,
    )


__all__ = ["TemplateModel"]
