"""Прокси-обёртки над ``LoggerStore``: единичный канал и tee (fan-out).

Прокси нужны, чтобы ``_LOG = get_logger(...)`` на уровне модуля видел
замены фабрики, выполненные позже через ``set_logger_factory``: каждый
вызов лога резолвится через ``LoggerStore`` на актуальный инстанс.
"""

from __future__ import annotations

from typing import Any

from src.core.loggers.logger_protocol import CoreLoggerProtocol
from src.core.loggers.logger_store import DEFAULT_CHANNEL, LoggerStore


class _LoggerProxy:
    """Прокси одного канала."""

    def __init__(self, channel: str = DEFAULT_CHANNEL) -> None:
        self._channel = channel

    def set_level(self, level: int | str) -> None:
        LoggerStore.get(self._channel).set_level(level)

    def debug(self, msg: Any, *a: Any, **kw: Any) -> None:
        LoggerStore.get(self._channel).debug(msg, *a, **kw)

    def info(self, msg: Any, *a: Any, **kw: Any) -> None:
        LoggerStore.get(self._channel).info(msg, *a, **kw)

    def warning(self, msg: Any, *a: Any, **kw: Any) -> None:
        LoggerStore.get(self._channel).warning(msg, *a, **kw)

    def error(self, msg: Any, *a: Any, **kw: Any) -> None:
        LoggerStore.get(self._channel).error(msg, *a, **kw)

    def exception(self, msg: Any, *a: Any, **kw: Any) -> None:
        LoggerStore.get(self._channel).exception(msg, *a, **kw)


class _TeeProxy:
    """Прокси-фан-аут: каждый вызов транслируется во все каналы."""

    def __init__(self, channels: tuple[str, ...]) -> None:
        self._channels = channels

    def set_level(self, level: int | str) -> None:
        for ch in self._channels:
            LoggerStore.get(ch).set_level(level)

    def debug(self, msg: Any, *a: Any, **kw: Any) -> None:
        for ch in self._channels:
            LoggerStore.get(ch).debug(msg, *a, **kw)

    def info(self, msg: Any, *a: Any, **kw: Any) -> None:
        for ch in self._channels:
            LoggerStore.get(ch).info(msg, *a, **kw)

    def warning(self, msg: Any, *a: Any, **kw: Any) -> None:
        for ch in self._channels:
            LoggerStore.get(ch).warning(msg, *a, **kw)

    def error(self, msg: Any, *a: Any, **kw: Any) -> None:
        for ch in self._channels:
            LoggerStore.get(ch).error(msg, *a, **kw)

    def exception(self, msg: Any, *a: Any, **kw: Any) -> None:
        for ch in self._channels:
            LoggerStore.get(ch).exception(msg, *a, **kw)


def get_logger(*channels: str) -> CoreLoggerProtocol:
    """Прокси одного или нескольких каналов. Без аргументов — канал ``core``."""
    if not channels:
        return _LoggerProxy(DEFAULT_CHANNEL)
    if len(channels) == 1:
        return _LoggerProxy(channels[0])
    return _TeeProxy(channels)


__all__ = ["_LoggerProxy", "_TeeProxy", "get_logger"]
