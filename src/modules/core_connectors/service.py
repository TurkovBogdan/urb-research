"""Фасад модуля доступов: единственная дверь для остальных модулей и для API.

Потребителю обычно нужен не набор значений, а работающий коннектор — за этим сюда и ходят:
``open_connector(service)`` отдаёт экземпляр, связанный с записью доступа, либо
типизированный отказ (``UnknownConnector`` / ``AccessNotConfigured`` / ``ConnectorDisabled``
/ ``AccessUndecryptable``), по которому потребитель строит понятную причину вместо «сбой
сервиса».

Запись доступа правится тоже отсюда: фасад дёргает CRUD и сбрасывает кеш store'а, чтобы
следующий ``open_connector`` увидел новое значение — это и есть «правится в runtime».

Опрос живых показателей (баланс, проверка) идёт **по запросу** и под двойным бюджетом:
таймаут на вызов и общий дедлайн на выдачу. Расписаний и истории в модуле нет и не будет —
это дело мониторинга, который дёргает те же ``balance()`` и ``check()``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from typing import Any

from src.modules.core_connectors import settings
from src.modules.core_connectors.access import crud, crypto
from src.modules.core_connectors.access.model import (
    ACCESS_STATUS_ERROR,
    ACCESS_STATUS_OK,
    AccessDetail,
    AccessRow,
    AccessStatus,
    AccessView,
    CoreConnectorsAccess,
)
from src.modules.core_connectors.access.store import access_store
from src.modules.core_connectors.connectors.base import Connector, failure_text
from src.modules.core_connectors.connectors.groups import ConnectorGroup, groups
from src.modules.core_connectors.connectors.passport import (
    ConnectorBalance,
    ConnectorCheck,
    ConnectorPassport,
    field_descriptors,
)
from src.modules.core_connectors.connectors.registry import connectors_registry
from src.modules.core_connectors.errors import AccessNotConfigured, ConnectorsError

SECRET_UNCHANGED = crud.SECRET_UNCHANGED

_DEADLINE_MESSAGE = "Превышен дедлайн опроса"


async def open_connector(service: str, *, access: int | None = None) -> Connector:
    """Коннектор, связанный с записью доступа. Без указания записи берётся та, что по
    умолчанию для этого сервиса.

    Явно указанная запись обязана принадлежать этому же сервису: иначе опечатка в id
    отправила бы ключ одного вендора другому.
    """
    connector_cls = connectors_registry.get(service)
    row = (
        await crud.access_get(access)
        if access is not None
        else await crud.access_default_for(service)
    )
    if row is None:
        raise AccessNotConfigured(f"{service}: нет записи доступа")
    if row.connector != service:
        raise AccessNotConfigured(
            f"Запись доступа {row.id} принадлежит коннектору {row.connector!r}, а не {service!r}"
        )
    return connector_cls(await access_store.ready_values(row))


async def access_available(service: str) -> bool:
    """Готов ли сервис к работе: запись есть, включена и заполнена. Сети не касается."""
    row = await crud.access_default_for(service)
    if row is None:
        return False
    return access_store.row_status(row).status == ACCESS_STATUS_OK


def passports() -> list[ConnectorPassport]:
    """Паспорта всех зарегистрированных коннекторов — что вообще можно настроить."""
    return connectors_registry.passports()


def connector_groups() -> list[ConnectorGroup]:
    """Справочник групп в порядке показа — чем сервисы бывают по своей природе."""
    return groups()


# ── записи доступа: чтение ───────────────────────────────────────────────


async def access_rows(*, connector: str | None = None) -> list[AccessRow]:
    return [_row_view(row) for row in await crud.access_list(connector=connector)]


async def access_detail(access_id: int) -> AccessDetail | None:
    """Запись с значениями под форму: секреты подменены сентинелом, а не отданы."""
    row = await crud.access_get(access_id)
    if row is None:
        return None
    stored = dict(row.values or {})
    secret_keys = _secret_keys(row.connector)
    values = {
        key: (SECRET_UNCHANGED if key in secret_keys and value else str(value))
        for key, value in stored.items()
    }
    fields = _passport_fields(row, is_set=frozenset(k for k in secret_keys if stored.get(k)))
    return AccessDetail(**_row_fields(row), values=values, fields=fields)


async def access_views(
    *, connector: str | None = None, with_balance: bool = False
) -> list[AccessView]:
    """Записи со статусом и (по запросу) живым балансом — витрина раздела «Сервисы».

    Баланс снимается только у готовых записей коннекторов, которые его умеют; сбой и
    просрочка одного коннектора остаются в его карточке.
    """
    rows = await crud.access_list(connector=connector)
    views = [
        AccessView(**_row_fields(row), has_balance=_has_balance(row.connector))
        for row in rows
    ]
    if with_balance:
        await _fill_balances(rows, views)
    return views


async def access_balance(access_id: int) -> ConnectorBalance:
    """Баланс одной записи — с таймаутом на вызов, но без общего дедлайна (запрос точечный)."""
    connector = await open_connector_by_id(access_id)
    return await _balance_within_timeout(connector)


async def check_access(access_id: int) -> ConnectorCheck:
    """Живая проверка доступа: дошли ли до сервиса и за сколько."""
    try:
        connector = await open_connector_by_id(access_id)
    except ConnectorsError as exc:
        return ConnectorCheck(ok=False, error=str(exc))
    try:
        return await asyncio.wait_for(connector.check(), timeout=settings.balance_timeout())
    except TimeoutError:
        return ConnectorCheck(ok=False, error=_DEADLINE_MESSAGE)


async def open_connector_by_id(access_id: int) -> Connector:
    """Коннектор конкретной записи (её сервис берётся из строки)."""
    row = await crud.access_get(access_id)
    if row is None:
        raise AccessNotConfigured(f"Записи доступа {access_id} нет")
    return connectors_registry.get(row.connector)(await access_store.ready_values(row))


# ── записи доступа: запись ───────────────────────────────────────────────


async def create_access(
    *,
    connector: str,
    values: Mapping[str, str] | None = None,
    enabled: bool = True,
) -> AccessRow:
    row = await crud.access_create(connector=connector, values=values, enabled=enabled)
    access_store.invalidate(row.id)
    return _row_view(row)


async def update_access(
    access_id: int,
    *,
    enabled: bool | None = None,
    values: Mapping[str, str] | None = None,
    clear: Iterable[str] = (),
) -> AccessRow | None:
    row = await crud.access_update(access_id, enabled=enabled, values=values, clear=clear)
    access_store.invalidate(access_id)
    return _row_view(row) if row is not None else None


async def delete_access(access_id: int) -> None:
    await crud.access_delete(access_id)
    access_store.invalidate(access_id)


async def seal_plaintext_secrets() -> list[int]:
    """Дошифровать секреты, лежащие открытым текстом. Возвращает затронутые записи.

    Ключ появляется позже записей — на существующей установке он выписывается при первом
    старте новой версии, когда доступы уже перенесены. Без этого шага состояние было бы
    лживым: шифрование включено, а половина базы открыта. Повторный вызов ничего не
    делает — шифртекст распознаётся по префиксу.
    """
    if not crypto.encryption_enabled():
        return []
    sealed: list[int] = []
    for row in await crud.access_list():
        plaintext = _plaintext_secrets(row)
        if not plaintext:
            continue
        await update_access(row.id, values=plaintext)
        sealed.append(row.id)
    return sealed


def _plaintext_secrets(row: CoreConnectorsAccess) -> dict[str, str]:
    """Секретные поля записи, лежащие открыто; чужой коннектор — не наше дело."""
    secret_keys = _secret_keys(row.connector)
    return {
        key: str(value)
        for key, value in (row.values or {}).items()
        if key in secret_keys and value and not crypto.is_encrypted(str(value))
    }


# ── сборка представлений ─────────────────────────────────────────────────


def _row_fields(row: CoreConnectorsAccess) -> dict[str, Any]:
    """Общая часть всех трёх представлений записи.

    Именно поля, а не готовый ``AccessRow``: собирать из него `AccessView`/`AccessDetail`
    пришлось бы через `model_dump()`, то есть гонять даты в строку и обратно на каждой
    строке списка.
    """
    return {
        "id": row.id,
        "enabled": row.enabled,
        "connector": row.connector,
        "connector_name": _connector_name(row.connector),
        "is_default": row.is_default,
        "status": access_store.row_status(row),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _row_view(row: CoreConnectorsAccess) -> AccessRow:
    return AccessRow(**_row_fields(row))


def _connector_name(service: str) -> str:
    """Имя из паспорта; пусто, если коннектор снят с регистрации — запись это переживает."""
    return connectors_registry.get(service).NAME if connectors_registry.has(service) else ""


def _secret_keys(service: str) -> frozenset[str]:
    if not connectors_registry.has(service):
        return frozenset()
    return connectors_registry.get(service).secret_keys()


def _has_balance(service: str) -> bool:
    return connectors_registry.has(service) and connectors_registry.get(service).HAS_BALANCE


def _passport_fields(row: CoreConnectorsAccess, *, is_set: frozenset[str]) -> list[dict]:
    if not connectors_registry.has(row.connector):
        return []
    return field_descriptors(connectors_registry.get(row.connector).FIELDS, is_set=is_set)


async def _fill_balances(
    rows: list[CoreConnectorsAccess], views: list[AccessView]
) -> None:
    """Снять баланс у готовых записей параллельно, уложившись в общий дедлайн."""
    pollable = [
        (row, view)
        for row, view in zip(rows, views)
        if view.has_balance and view.status.status == ACCESS_STATUS_OK
    ]
    if not pollable:
        return
    tasks = {
        asyncio.create_task(_row_balance(row)): view for row, view in pollable
    }
    done, pending = await asyncio.wait(tasks, timeout=settings.poll_deadline())
    for task in pending:
        task.cancel()
        view = tasks[task]
        view.balance = _balance_error(view, _DEADLINE_MESSAGE)
        view.status = AccessStatus(status=ACCESS_STATUS_ERROR, detail=_DEADLINE_MESSAGE)
    # Дожидаемся снятия: без этого отменённые задачи доигрываются уже после ответа и
    # роняют в лог «Task was destroyed but it is pending».
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
    for task in done:
        view = tasks[task]
        view.balance = task.result()
        if view.balance.error:
            view.status = AccessStatus(status=ACCESS_STATUS_ERROR, detail=view.balance.error)


async def _row_balance(row: CoreConnectorsAccess) -> ConnectorBalance:
    """Баланс записи; любой сбой остаётся значением в DTO — соседние карточки не страдают."""
    try:
        connector = connectors_registry.get(row.connector)(
            await access_store.ready_values(row)
        )
        return await _balance_within_timeout(connector)
    except Exception as exc:  # noqa: BLE001 — сбой одного коннектора не роняет выдачу
        return ConnectorBalance(
            service=row.connector,
            name=_connector_name(row.connector),
            error=failure_text(exc),
        )


async def _balance_within_timeout(connector: Connector) -> ConnectorBalance:
    try:
        return await asyncio.wait_for(connector.balance(), timeout=settings.balance_timeout())
    except TimeoutError:
        return ConnectorBalance(
            service=connector.SERVICE, name=connector.NAME, error=_DEADLINE_MESSAGE
        )


def _balance_error(view: AccessView, message: str) -> ConnectorBalance:
    return ConnectorBalance(service=view.connector, name=view.connector_name, error=message)


__all__ = [
    "open_connector",
    "open_connector_by_id",
    "access_available",
    "passports",
    "connector_groups",
    "access_rows",
    "access_detail",
    "access_views",
    "access_balance",
    "check_access",
    "create_access",
    "update_access",
    "delete_access",
    "seal_plaintext_secrets",
    "SECRET_UNCHANGED",
]
