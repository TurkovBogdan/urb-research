"""Здоровье файловой базы SQLite: размер журнала и две проверки целостности.

У движка почти нет громких отказов. Голодание чекпойнта не логируется и не
возвращает ошибку — растущий файл-спутник рядом с небольшой базой единственный
его признак. А ``integrity_check`` не смотрит на внешние ключи вовсе, поэтому
проверок две, а не одна.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from src.core.config import get_config
from src.core.database import get_engine
from src.core.scheduler import CoreTaskBase, TaskContext

_WAL_SHARE_TO_WARN = 0.25


class SqliteHealthTask(CoreTaskBase):
    """Раз в час: размер журнала относительно базы + целостность страниц и ссылок."""

    MODULE = "core"
    CODE = "sqlite_health"
    NAME = "SQLite health"
    DESCRIPTION = (
        "Раз в час: размер файла-спутника WAL относительно базы (голодание чекпойнта "
        "ничем больше себя не выдаёт), quick_check и foreign_key_check."
    )
    SCHEDULE = "17 * * * *"
    TTL = 300

    @staticmethod
    async def handle(ctx: TaskContext) -> None:
        database_file = get_config().sqlite_file
        if database_file is None or not database_file.exists():
            await ctx.info("провайдер не файловый sqlite — проверять нечего")
            return

        database_bytes = database_file.stat().st_size
        wal_bytes = _companion_size(database_file)
        await ctx.info(
            "база %.1f МБ, журнал %.1f МБ",
            database_bytes / 1024 / 1024,
            wal_bytes / 1024 / 1024,
        )
        if database_bytes and wal_bytes > database_bytes * _WAL_SHARE_TO_WARN:
            await ctx.warn(
                "журнал разросся до %.0f%% размера базы — чекпойнт не доводит работу до конца",
                wal_bytes / database_bytes * 100,
            )

        engine = get_engine()
        assert engine is not None, "init_database() not called"
        async with engine.connect() as connection:
            pages = (await connection.execute(text("PRAGMA quick_check"))).scalar()
            violations = (await connection.execute(text("PRAGMA foreign_key_check"))).all()
        if pages != "ok":
            await ctx.error("quick_check: %s", pages)
        if violations:
            await ctx.error("нарушений ссылочной целостности: %d", len(violations))


def _companion_size(database_file: Path) -> int:
    companion = database_file.with_name(f"{database_file.name}-wal")
    return companion.stat().st_size if companion.exists() else 0


__all__ = ["SqliteHealthTask"]
