"""Перезапуск процесса для применения нового ``.env`` (Config читается на старте).

Способ зависит от режима, иначе ловим «port already in use»:

- **hot-reload (dev):** uvicorn держит слушающий сокет через свой reload-супервизор.
  ``os.execv`` поднял бы второй процесс на тот же порт → конфликт. Поэтому просто
  «трогаем» watched-файл в ``src/`` — супервизор штатно пересобирает воркер
  (re-import ``server.py`` → ``Config()`` перечитывает ``.env``), порт не перебиндивается.
- **без reload (prod/одиночный процесс):** ``os.execv`` замещает образ тем же
  ``python src/app.py …`` — порт освобождается заместившимся процессом.

Планируется с короткой задержкой, чтобы HTTP-ответ успел уйти до перезапуска.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from src.core.loggers import get_logger

_LOG = get_logger()

# Точка входа src/app.py — она под reload_dirs uvicorn (--reload watch по src/).
_WATCHED_ENTRY = Path(__file__).resolve().parents[2] / "app.py"


def _reexec() -> None:
    os.execv(sys.executable, [sys.executable, *sys.argv])


def _trigger_reload() -> None:
    # Обновляем mtime watched-файла → uvicorn --reload пересобирает воркер.
    _WATCHED_ENTRY.touch()


def schedule_restart(*, hot_reload: bool, delay: float = 0.5) -> None:
    """Запланировать перезапуск через ``delay`` секунд (после отправки текущего ответа)."""
    action = _trigger_reload if hot_reload else _reexec
    how = "uvicorn reload (touch src)" if hot_reload else "os.execv"
    _LOG.warning("core_setup: restart in %.1fs via %s — .env будет перечитан", delay, how)
    asyncio.get_running_loop().call_later(delay, action)


__all__ = ["schedule_restart"]
