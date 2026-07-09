"""Резолвер рантайм-путей и типизированные пути приложения.

Работа в двух режимах:

- **Dev** (запуск из исходников): корень — `<project>/runtime/<env>`,
  где `env` берётся из `APP_ENV` (по умолчанию `dev`).
- **Prod** (PyInstaller-бинарь, `sys.frozen`): корень — директория, где лежит
  исполняемый файл. `logs/`, `cache/` и пр. кладутся рядом с бинарём.

Пользоваться через `AppPath.from_root()` — низкоуровневые функции
(`resolve_runtime_root`, `project_root`) нужны только для редких случаев.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

# `src/core/app_path.py` → `<project>/`
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ── Резолвер рантайм-корня ───────────────────────────────────────────────────

def resolve_runtime_root() -> Path:
    """Frozen → рядом с бинарём; source → `<project>/runtime/<APP_ENV>` (default `dev`)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    env = os.getenv("APP_ENV", "dev")
    return _PROJECT_ROOT / "runtime" / env


def project_root() -> Path:
    """Корень репозитория (`<project>/`) — для закоммиченных артефактов вроде
    собранного фронта `web/dist`. Это НЕ рантайм-корень (см. resolve_runtime_root)."""
    return _PROJECT_ROOT


# ── Типизированные пути приложения ───────────────────────────────────────────

@dataclass(frozen=True)
class AppPath:
    """Каноничные пути приложения; все поля — абсолютные."""

    root: Path
    logs: Path
    cache: Path
    user: Path
    import_: Path
    tmp: Path
    storage_public: Path
    storage_protected: Path
    storage_private: Path

    @staticmethod
    def from_root(root: Path | None = None) -> "AppPath":
        """Собрать `AppPath` от заданного `root` или от резолвера рантайм-корня."""
        r = Path(root).resolve() if root is not None else resolve_runtime_root()
        return AppPath(
            root=r,
            logs=r / "logs",
            cache=r / "cache",
            user=r / "user",
            import_=r / "import",
            tmp=r / "tmp",
            storage_public=r / "storage" / "public",
            storage_protected=r / "storage" / "protected",
            storage_private=r / "storage" / "private",
        )


def ensure_dirs(paths: AppPath) -> None:
    """Создать все стандартные директории `AppPath` (idempotent)."""
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.logs.mkdir(parents=True, exist_ok=True)
    paths.cache.mkdir(parents=True, exist_ok=True)
    paths.user.mkdir(parents=True, exist_ok=True)
    paths.import_.mkdir(parents=True, exist_ok=True)
    paths.tmp.mkdir(parents=True, exist_ok=True)
    paths.storage_public.mkdir(parents=True, exist_ok=True)
    paths.storage_protected.mkdir(parents=True, exist_ok=True)
    paths.storage_private.mkdir(parents=True, exist_ok=True)


__all__ = ["AppPath", "ensure_dirs", "project_root", "resolve_runtime_root"]
