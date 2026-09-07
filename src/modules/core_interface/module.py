"""Модуль ``core_interface`` — настройки интерфейса пользователя в базе.

Отвечает на один вопрос: каким человек оставил внешний вид приложения — тема, гарнитуры,
зона чтения, оформление схем, раскладки списков. Хранит только отклонения от умолчаний
(таблица ``core_interface_settings``), сами умолчания объявлены в ``registry.py``.

Не ядро, потому что ядро этих значений не потребляет: ни одна серверная строка не читает
тему или гарнитуру — это данные для браузера. Рассчитан на сценарий одного пользователя
без учётных записей: у настройки нет владельца, ключ уникален сам по себе.

Ни задач, ни guard'ов, ни MCP-сервера, ни схемы настроек модуля: это хранилище с проверкой.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from fastapi import FastAPI

from src.core.config import Config
from src.core.loggers import get_logger
from src.core.module import Module
from src.modules.core_interface import models  # noqa: F401 — регистрирует таблицу в Base.metadata
from src.modules.core_interface import crud
from src.modules.core_interface.api import internal_router
from src.modules.core_interface.constants import LOG_CHANNEL
from src.modules.core_interface.registry import SETTINGS, validate_registry

_HERE = Path(__file__).resolve().parent
_LOG = get_logger(LOG_CHANNEL)


class CoreInterfaceModule(Module):
    name: ClassVar[str] = "core_interface"
    description: ClassVar[str] = (
        "Настройки интерфейса пользователя: тема, гарнитуры, оформление документа и схем."
    )
    migrations_dir = _HERE / "migrations" / "versions"
    internal_router = internal_router
    internal_router_prefix = "/core/interface"

    def configure(self, app: FastAPI, config: Config) -> None:
        """Самопроверка реестра — здесь, а не в ``on_startup``: сборка приложения падает от
        исключения, а lifespan свои ловит и пишет в лог, и кривая карта уехала бы молча."""
        validate_registry()

    async def on_startup(self, app: FastAPI) -> None:
        """Уборка ключей, снятых с производства прошлой выкладкой."""
        removed = await crud.prune_unknown(list(SETTINGS))
        if removed:
            _LOG.info("core_interface: удалено настроек вне реестра: %d", removed)


__all__ = ["CoreInterfaceModule"]
