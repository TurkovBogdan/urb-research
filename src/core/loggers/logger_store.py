"""Реестр каналов логирования: имя → инстанс ``CoreLoggerProtocol``.

Один логгер на канал, лениво создаётся фабрикой. По умолчанию фабрика —
``CoreLogger`` с файлом ``logs/<channel>.log``. Bootstrap (``apps/app/server.py``)
заменяет фабрику на нужную (level из settings, кастомные пути).
"""

from __future__ import annotations

from typing import Callable

from src.core.loggers.logger_protocol import CoreLoggerProtocol

LoggerFactory = Callable[[str], CoreLoggerProtocol]

DEFAULT_CHANNEL = "core"


def _default_factory(channel: str) -> CoreLoggerProtocol:
    """Ленивый дефолт: ``CoreLogger`` с файлом ``logs/<channel>.log``.

    Существует, чтобы ранние импорты до ``set_factory`` не падали и в тестах
    не нужен был bootstrap. В нормальной сборке фабрику ставит app-bootstrap.
    """
    from src.core.app_path import AppPath, ensure_dirs
    from src.core.loggers.core_logger import CoreLogger

    paths = AppPath.from_root()
    ensure_dirs(paths)
    return CoreLogger(logs_dir=paths.logs, file_name=channel)


class LoggerStore:
    """Class-based runtime-хранилище логгеров по каналам."""

    _channels: dict[str, CoreLoggerProtocol] = {}
    _factory: LoggerFactory | None = None

    @classmethod
    def get(cls, channel: str = DEFAULT_CHANNEL) -> CoreLoggerProtocol:
        """Вернуть логгер канала. При отсутствии — создаст через фабрику."""
        if channel not in cls._channels:
            factory = cls._factory or _default_factory
            cls._channels[channel] = factory(channel)
        return cls._channels[channel]

    @classmethod
    def set(
        cls,
        logger: CoreLoggerProtocol | None,
        channel: str = DEFAULT_CHANNEL,
    ) -> None:
        """Зафиксировать логгер канала. ``None`` — снять; следующий ``get`` пересоздаст."""
        if logger is None:
            cls._channels.pop(channel, None)
        else:
            cls._channels[channel] = logger

    @classmethod
    def set_factory(cls, factory: LoggerFactory | None) -> None:
        """Заменить фабрику. Все ранее лениво созданные каналы сбрасываются."""
        cls._factory = factory
        cls._channels.clear()

    @classmethod
    def reset(cls) -> None:
        """Полный сброс: фабрика и все каналы."""
        cls._channels.clear()
        cls._factory = None


def set_logger_factory(factory: LoggerFactory | None) -> None:
    """Заменить фабрику каналов. Сбрасывает уже созданные инстансы."""
    LoggerStore.set_factory(factory)


__all__ = ["DEFAULT_CHANNEL", "LoggerFactory", "LoggerStore", "set_logger_factory"]
