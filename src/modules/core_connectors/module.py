"""Модуль ``core_connectors`` — доступы к внешним сервисам.

Отвечает на один вопрос: каким ключом и с какими параметрами код идёт в этот сервис и
разрешено ли туда идти. Хранит записи доступа (таблица ``core_connectors_access``, секреты
шифрованы), знает паспорт каждого коннектора, умеет проверить доступ и снять баланс — и не
делает больше ничего: ни выбора за потребителя, ни расписаний, ни истории.

Реестр коннекторов динамический: встроенные вносятся при импорте пакета ``connectors``,
чужой модуль вправе внести свои своим ``configure()`` или позже — состав виден следующему
запросу без перезапуска. Настройки модуля — только его собственные ручки (бюджет опроса);
креды в схеме настроек не живут.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from fastapi import FastAPI

from src.core.loggers import get_logger
from src.core.module import Module
from src.modules.core_connectors.access import crypto
from src.modules.core_connectors.access import model  # noqa: F401 — регистрирует модель в Base.metadata
from src.modules.core_connectors.access.legacy import import_legacy_accesses
from src.modules.core_connectors.api import internal_router
from src.modules.core_connectors.service import seal_plaintext_secrets
from src.modules.core_connectors.settings import SCHEMA

_HERE = Path(__file__).resolve().parent
_LOG = get_logger("core_connectors")


class CoreConnectorsModule(Module):
    name: ClassVar[str] = "core_connectors"
    description: ClassVar[str] = "Подключения к внешним сервисам: ключи, статусы, баланс."
    settings_schema = SCHEMA
    migrations_dir = _HERE / "migrations" / "versions"
    internal_router = internal_router
    internal_router_prefix = ""

    async def on_startup(self, app: FastAPI) -> None:
        """Разовый перенос кредов из старой схемы + дошифровка тех, что легли открыто."""
        imported = await import_legacy_accesses(self.store)
        if imported:
            _LOG.info("core_connectors: перенесены доступы %s", imported["connectors"])
        if not crypto.encryption_enabled():
            _LOG.warning("core_connectors: шифрование выключено — SECRETS_KEY не задан")
            return
        _LOG.info("core_connectors: мастер-ключ версии %s", crypto.master_key_version())
        sealed = await seal_plaintext_secrets()
        if sealed:
            _LOG.info("core_connectors: дошифрованы записи %s", sealed)


__all__ = ["CoreConnectorsModule"]
