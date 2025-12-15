# src/discordia/models/base.py
from __future__ import annotations

from typing import Any

from sqlmodel import SQLModel


class ValidatedSQLModel(SQLModel):
    """SQLModel base class that preserves Pydantic validation on __init__.

    SQLModel table models prioritize SQLAlchemy construction and bypass Pydantic
    validation by default. Discordia's models are used as both validated data
    objects and ORM entities, so we restore validation at instantiation time.
    """

    def __init__(self, **data: Any) -> None:
        # Initialize SQLAlchemy instrumentation (_sa_instance_state) first.
        super().__init__()

        # Preserve SQLAlchemy-managed attributes while running Pydantic validation.
        old_dict = self.__dict__.copy()

        # Validate and populate fields onto this instance (including defaults).
        self.__class__.__pydantic_validator__.validate_python(data, self_instance=self)

        # Pydantic may reset __dict__; merge back SQLAlchemy instrumentation.
        object.__setattr__(self, "__dict__", {**old_dict, **self.__dict__})
