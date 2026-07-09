"""Reusable ORM column mixins."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.types import timestamp


class SoftDeleteMixin:
    """Adds ``deleted_at`` column; non-null means the row is logically deleted."""

    deleted_at: Mapped[datetime | None] = mapped_column(timestamp(), nullable=True)


__all__ = ["SoftDeleteMixin"]
