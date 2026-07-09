"""Programmatic Alembic runner — собирает version_locations из Module-инстансов."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.module import Module

_ALEMBIC_DIR = Path(__file__).resolve().parent / "alembic"
_CORE_MIGRATIONS = (
    Path(__file__).resolve().parent.parent / "migrations" / "versions"
)


@dataclass(frozen=True)
class PendingRevision:
    """Одна миграция, ещё не накатанная на БД."""

    revision: str
    down_revision: str | tuple[str, ...] | None
    message: str
    path: str


@dataclass(frozen=True)
class MigrationStatus:
    """Снимок состояния миграций: где БД, куда должна прийти, что между ними."""

    current_heads: tuple[str, ...]
    target_heads: tuple[str, ...]
    pending: list[PendingRevision]  # в порядке применения (от старых к новым)

    @property
    def up_to_date(self) -> bool:
        return not self.pending


class AlembicRunner:
    """Применяет миграции через Alembic programmatic API."""

    def __init__(
        self,
        modules: Sequence[Module],
        script_root: Path | None = None,
    ) -> None:
        self._modules = list(modules)
        self._script_root = (script_root or _ALEMBIC_DIR).resolve()

    def _version_locations(self) -> list[Path]:
        locations: list[Path] = [_CORE_MIGRATIONS]
        locations.extend(
            m.migrations_dir for m in self._modules if m.migrations_dir is not None
        )
        return locations

    def _base_config(self) -> AlembicConfig:
        """Config без подключения — для offline/script-операций (ScriptDirectory)."""
        cfg = AlembicConfig()
        cfg.set_main_option("script_location", str(self._script_root))
        cfg.set_main_option("path_separator", "os")
        locations = self._version_locations()
        if locations:
            import os
            cfg.set_main_option(
                "version_locations",
                os.pathsep.join(str(p) for p in locations),
            )
        return cfg

    def _build_config(self, connection: Connection) -> AlembicConfig:
        cfg = self._base_config()
        cfg.attributes["connection"] = connection
        return cfg

    def _do_upgrade(self, connection: Connection) -> None:
        cfg = self._build_config(connection)
        command.upgrade(cfg, "heads")

    def _do_status(self, connection: Connection) -> MigrationStatus:
        script = ScriptDirectory.from_config(self._base_config())
        current = tuple(MigrationContext.configure(connection).get_current_heads())
        heads = tuple(script.get_heads())
        # pending = предки всех target-head'ов, которых нет среди применённых.
        # Применённые = current head'ы + все их предки. Считаем именно так (а не
        # iterate_revisions(heads, current)): тот вариант отдаёт лишь ПОТОМКОВ
        # current, поэтому новый независимый корень (модуль с down_revision=None,
        # добавленный к уже наполненной БД) терялся → ложный up_to_date.
        applied = {s.revision for s in script.iterate_revisions(current, "base")}
        pending = [
            s
            for s in script.iterate_revisions(heads, "base")
            if s.revision not in applied
        ]
        pending.reverse()  # base → head: порядок применения
        return MigrationStatus(
            current_heads=current,
            target_heads=heads,
            pending=[
                PendingRevision(
                    revision=s.revision,
                    down_revision=s.down_revision,
                    message=(s.doc or "").strip(),
                    path=str(s.path),
                )
                for s in pending
            ],
        )

    async def status(self, engine: AsyncEngine) -> MigrationStatus:
        """Dry-run сверка: текущие/целевые head'ы и список pending-миграций (ничего не меняет)."""
        async with engine.connect() as connection:
            return await connection.run_sync(self._do_status)

    async def upgrade_head(self, engine: AsyncEngine) -> None:
        """Боевая миграция: накатить ядро и все модули до head."""
        async with engine.connect() as connection:
            await connection.run_sync(self._do_upgrade)


__all__ = ["AlembicRunner", "MigrationStatus", "PendingRevision"]
