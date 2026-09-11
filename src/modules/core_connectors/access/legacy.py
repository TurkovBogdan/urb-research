"""Разовый перенос кредов из старой схемы настроек в записи доступа.

До этой версии токены лежали строками настроек модуля (``tavily_api_key``,
``xai_management_api_key``, тумблеры ``*_gateway_enabled``). Перенос делает **не Alembic**:
сопоставление старых ключей с полями паспорта — знание кода, а значения на выходе надо ещё
и зашифровать, то есть нужны реестр, паспорт и слой шифрования. Всё это доступно только в
``on_startup``, где база уже поднята.

Отображение выводится из паспорта, а не выписывается таблицей: старый ключ — это
``<сервис>_<поле>`` (``xai_management_api_key`` → поле ``management_api_key`` коннектора
``xai``), тумблер — ``<сервис>_gateway_enabled``. Пустое в настройках может подхватиться
из окружения (``TAVILY_API_KEY``) — это разовый посев для развёртывания с нуля, а не
постоянная цепочка разрешения: после импорта значение живёт в записи.

Старые строки настроек **не удаляются**: они остаются страховкой до следующего релиза (их
ключей больше нет в схеме, поэтому реестр настроек просто игнорирует их как «сирот»).
Отметка о переносе лежит в состоянии модуля — повтор возможен только после её сброса.
"""

from __future__ import annotations

import os
from typing import Any

from src.core.crud import module_settings
from src.core.module_state import ModuleStore
from src.modules.core_connectors.access import crud
from src.modules.core_connectors.connectors import BUILTIN_CONNECTORS

LEGACY_IMPORT_MARK = "legacy_settings_import"

_LEGACY_MODULE = "core_connectors"
_ENABLED_SUFFIX = "_gateway_enabled"


async def import_legacy_accesses(store: ModuleStore) -> dict[str, Any] | None:
    """Создать записи доступа по старым настройкам. ``None`` — импорт уже был."""
    if await store.get(LEGACY_IMPORT_MARK) is not None:
        return None

    legacy = {row.key: row.value for row in await module_settings.list_for_module(_LEGACY_MODULE)}
    imported: list[str] = []
    for connector in BUILTIN_CONNECTORS:
        values = _legacy_values(connector, legacy)
        if not _was_configured(connector, values, legacy):
            continue
        if await crud.access_default_for(connector.SERVICE) is not None:
            continue
        await crud.access_create(
            connector=connector.SERVICE,
            values=values,
            enabled=legacy.get(f"{connector.SERVICE}{_ENABLED_SUFFIX}") != "false",
        )
        imported.append(connector.SERVICE)

    mark = {"connectors": imported}
    await store.set(LEGACY_IMPORT_MARK, mark)
    return mark


def _legacy_values(connector: type, legacy: dict[str, str]) -> dict[str, str]:
    """Значения полей паспорта по старым ключам; пустое в настройках — из окружения.

    Значение подрезается по краям: токены попадали в старые настройки вставкой из буфера,
    и лишний пробел ломает заголовок авторизации молча.
    """
    values: dict[str, str] = {}
    for field in connector.FIELDS:
        legacy_key = f"{connector.SERVICE}_{field.key}"
        value = (legacy.get(legacy_key) or os.environ.get(legacy_key.upper(), "")).strip()
        if value:
            values[field.key] = value
    return values


def _was_configured(connector: type, values: dict[str, str], legacy: dict[str, str]) -> bool:
    """Пользовался ли этой связкой прежний конфиг — только тогда заводим запись.

    Обычно признак — непустое значение. Но у коннектора без обязательных полей (локальный
    демон с выключенной авторизацией) заполнять нечего, и он всё равно работал: там
    признаком служит сам факт старой строки-тумблера.
    """
    if values:
        return True
    return not connector.REQUIRED and f"{connector.SERVICE}{_ENABLED_SUFFIX}" in legacy


__all__ = ["LEGACY_IMPORT_MARK", "import_legacy_accesses"]
