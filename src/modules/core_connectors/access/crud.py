"""Запись доступа: единственное место, где значения полей пишутся в базу.

Разделение обязанностей вокруг значений: **CRUD пишет** (сверяет поля с паспортом, шифрует
секреты, обновляет строку и сбрасывает кеш), **store читает**, **crypto превращает** одно в
другое. Прямого пути от потребителя к таблице нет.

Контракт записи секрета — тот же, что у настроек ядра, и по той же причине: наружу секрет
уходит сентинелом, поэтому пустая строка на входе значит «я это поле не трогал», а не
«сотри его». Отличие одно: у записи доступа нет «сброса к умолчанию», поэтому очистка
выражается явным списком полей ``clear``.

Шифрование врезано здесь же: при создании записи рождается её ключ данных (завёрнутый
мастер-ключом), при записи значений секреты запечатываются им. Мастер-ключа нет —
значения пишутся открытым текстом, это законное состояние «шифрование выключено».
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from sqlalchemy import delete as sa_delete, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import session_scope, write_scope
from src.core.utils.date import utc_now
from src.modules.core_connectors.access import crypto
from src.modules.core_connectors.access.model import CoreConnectorsAccess
from src.modules.core_connectors.connectors.registry import connectors_registry

SECRET_UNCHANGED = "NOT_CHANGED"


async def access_get(access_id: int) -> CoreConnectorsAccess | None:
    async with session_scope() as s:
        return (
            await s.execute(
                select(CoreConnectorsAccess).where(CoreConnectorsAccess.id == access_id)
            )
        ).scalar_one_or_none()


async def access_list(*, connector: str | None = None) -> list[CoreConnectorsAccess]:
    stmt = select(CoreConnectorsAccess).order_by(
        CoreConnectorsAccess.connector, CoreConnectorsAccess.id
    )
    if connector:
        stmt = stmt.where(CoreConnectorsAccess.connector == connector)
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def access_default_for(connector: str) -> CoreConnectorsAccess | None:
    """Запись по умолчанию для коннектора; при единственной записи — она и есть."""
    stmt = (
        select(CoreConnectorsAccess)
        .where(CoreConnectorsAccess.connector == connector)
        .order_by(CoreConnectorsAccess.is_default.desc(), CoreConnectorsAccess.id)
        .limit(1)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


async def access_create(
    *,
    connector: str,
    values: Mapping[str, str] | None = None,
    enabled: bool = True,
    is_default: bool = True,
) -> CoreConnectorsAccess:
    """Создать запись доступа. Коннектор обязан быть в реестре — иначе неизвестно, из каких
    полей она состоит. Значения пишутся вторым шагом: связывание шифртекста включает id
    записи, а он появляется только после вставки."""
    connectors_registry.get(connector)
    data_key, key_version = crypto.new_data_key() if crypto.encryption_enabled() else (None, None)
    async with write_scope() as s:
        row = CoreConnectorsAccess(
            enabled=enabled,
            connector=connector,
            is_default=is_default,
            values={},
            data_key=data_key,
            key_version=key_version,
        )
        s.add(row)
        await s.flush()
        row.values = _sealed_values(row, dict(values or {}))
        if is_default:
            await _demote_siblings(s, row)
        await s.flush()
        return row


async def access_update(
    access_id: int,
    *,
    enabled: bool | None = None,
    is_default: bool | None = None,
    values: Mapping[str, str] | None = None,
    clear: Iterable[str] = (),
) -> CoreConnectorsAccess | None:
    """Изменить запись. Переданы только те поля, что меняются; ``clear`` стирает
    перечисленные поля (пустая строка этого не делает — см. контракт секрета)."""
    async with write_scope() as s:
        row = (
            await s.execute(
                select(CoreConnectorsAccess).where(CoreConnectorsAccess.id == access_id)
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        if enabled is not None:
            row.enabled = enabled
        if is_default is not None:
            row.is_default = is_default
            if is_default:
                await _demote_siblings(s, row)
        if values is not None or clear:
            row.values = _sealed_values(row, dict(values or {}), clear=frozenset(clear))
        row.updated_at = utc_now()
        await s.flush()
        return row


async def access_delete(access_id: int) -> None:
    async with write_scope() as s:
        await s.execute(
            sa_delete(CoreConnectorsAccess).where(CoreConnectorsAccess.id == access_id)
        )


async def _demote_siblings(session: AsyncSession, row: CoreConnectorsAccess) -> None:
    """Умолчание у коннектора одно: назначая его записи, снимаем флаг с остальных.

    Иначе ``access_default_for`` выбирал бы из двух «умолчаний» по порядку id — то есть
    молча и не тем, что человек отметил последним.
    """
    await session.execute(
        sa_update(CoreConnectorsAccess)
        .where(
            CoreConnectorsAccess.connector == row.connector,
            CoreConnectorsAccess.id != row.id,
        )
        .values(is_default=False)
    )


def _sealed_values(
    row: CoreConnectorsAccess,
    incoming: dict[str, str],
    *,
    clear: frozenset[str] = frozenset(),
) -> dict[str, str]:
    """Новое содержимое колонки значений: известные паспорту поля, секреты — шифртекстом.

    Поле, которого нет в паспорте, отбрасывается: иначе запись копила бы мусор от
    переименований и опечаток.
    """
    connector_cls = connectors_registry.get(row.connector)
    secret_keys = connector_cls.secret_keys()
    stored = dict(row.values or {})
    data_key = _data_key(row)

    for field in connector_cls.FIELDS:
        key = field.key
        if key in clear:
            stored.pop(key, None)
            continue
        if key not in incoming:
            continue
        value = incoming[key]
        if key in secret_keys and value in ("", SECRET_UNCHANGED):
            continue
        stored[key] = (
            crypto.encrypt_value(
                value,
                data_key=data_key,
                access_id=row.id,
                field_key=key,
                key_version=row.key_version or "",
            )
            if key in secret_keys and data_key is not None
            else value
        )
    known_keys = {field.key for field in connector_cls.FIELDS}
    return {key: value for key, value in stored.items() if key in known_keys}


def _data_key(row: CoreConnectorsAccess) -> bytes | None:
    """Ключ данных записи; ``None`` — шифрование выключено (значения пишутся открыто).

    Ключ рождается лениво: запись, созданная без мастер-ключа, получит его при первой
    записи после того, как ключ появился, — новые значения уже уедут шифртекстом.
    """
    if not crypto.encryption_enabled():
        return None
    if not row.data_key:
        row.data_key, row.key_version = crypto.new_data_key()
    return crypto.unwrap_data_key(row.data_key, row.key_version or "")


__all__ = [
    "SECRET_UNCHANGED",
    "access_get",
    "access_list",
    "access_default_for",
    "access_create",
    "access_update",
    "access_delete",
]
