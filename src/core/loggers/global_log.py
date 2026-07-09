"""Глобальный лог: тиирует весь stdout/stderr в logs/global.log.

Вызывать как можно раньше при старте процесса — до любой другой инициализации.
Работает для GUI, MCP-серверов и любых других точек входа платформы.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from src.core.app_path import resolve_runtime_root


class _TeeStream:
    def __init__(self, original: TextIO, log_file: Path) -> None:
        self._original = original
        self._file     = log_file.open("a", encoding="utf-8", buffering=1)

    def write(self, text: str) -> int:
        # файл — первым, чтобы исключение в оригинальном потоке не блокировало запись
        self._file.write(text)
        if self._original is not None:
            try:
                self._original.write(text)
                self._original.flush()
            except Exception:
                pass
        return len(text)

    def flush(self) -> None:
        self._file.flush()
        if self._original is not None:
            try:
                self._original.flush()
            except Exception:
                pass

    def fileno(self) -> int:
        if self._original is not None:
            return self._original.fileno()
        raise OSError("stream has no fileno")

    def isatty(self) -> bool:
        return False


def install() -> None:
    """Перенаправить stdout и stderr: писать в оригинал + logs/global.log."""
    logs_dir = resolve_runtime_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "app.log"

    # захватываем sys.stdout/stderr как они есть сейчас (IDE может уже заменить их)
    sys.stdout = _TeeStream(sys.stdout, log_file)  # type: ignore[assignment]
    sys.stderr = _TeeStream(sys.stderr, log_file)  # type: ignore[assignment]


__all__ = ["install"]
