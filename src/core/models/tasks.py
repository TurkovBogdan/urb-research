"""Модели запусков фоновых задач и их логов."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp


class CoreTaskStatus(str, Enum):
    running = "running"
    success = "success"
    error = "error"


class CoreTaskLogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"


class CoreTask(Base):
    __tablename__ = "core_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[CoreTaskStatus] = mapped_column(
        SAEnum(CoreTaskStatus, native_enum=False, length=16), index=True
    )
    module: Mapped[str] = mapped_column(String(64))
    code: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime] = mapped_column(timestamp(), index=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(
        timestamp(), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        timestamp(), nullable=True
    )

    __table_args__ = (
        Index("ix_core_tasks_module_code", "module", "code"),
        Index(
            "uq_core_tasks_running_pair",
            "module",
            "code",
            unique=True,
            sqlite_where=text("status = 'running'"),
            postgresql_where=text("status = 'running'"),
        ),
    )


class CoreTaskLog(Base):
    __tablename__ = "core_tasks_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("core_tasks.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[CoreTaskLogLevel] = mapped_column(
        SAEnum(CoreTaskLogLevel, native_enum=False, length=8)
    )
    message: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(timestamp(), index=True)


__all__ = ["CoreTask", "CoreTaskLog", "CoreTaskStatus", "CoreTaskLogLevel"]
