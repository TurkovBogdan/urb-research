"""CRUD таблицы ``core_interface_settings``. Каждая функция открывает свой scope сама.

Наружу (в HTTP) выведены только чтение и пачечная запись. Удаление ручки не имеет: человек
сбрасывает настройку **к умолчанию**, а то, что хранилище при этом убирает строку, — его
внутреннее дело. Отсюда три оставшиеся функции: ``delete_many`` зовёт обработчик сброса,
``prune_unknown`` — уборка на подъёме модуля, ``delete_all`` держится для миграций.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import session_scope, write_scope
from src.core.utils.date import utc_now
from src.modules.core_interface.models import InterfaceSetting


def _insert_for(session: AsyncSession):
    dialect = session.bind.dialect.name if session.bind else "postgresql"
    if dialect == "sqlite":
        return sqlite_insert
    return pg_insert


async def list_all() -> dict[str, Any]:
    """Карта отклонений целиком: строк здесь десятки, выборка всегда полная."""
    async with session_scope() as s:
        rows = (await s.execute(select(InterfaceSetting))).scalars().all()
        return {row.key: row.value for row in rows}


async def upsert_many(values: Mapping[str, Any]) -> None:
    """Пачка в одной пишущей транзакции: накопленное за дебаунс применяется целиком.

    ``created_at`` в ветке обновления не трогается — время появления ключа переживает
    любое число правок.
    """
    if not values:
        return
    async with write_scope() as s:
        insert = _insert_for(s)
        now = utc_now()
        stmt = insert(InterfaceSetting).values(
            [
                {"key": key, "value": value, "created_at": now, "updated_at": now}
                for key, value in values.items()
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={"value": stmt.excluded.value, "updated_at": now},
        )
        await s.execute(stmt)


async def delete_many(keys: Sequence[str]) -> None:
    """Снять переопределения: строки исчезают, снова действует умолчание из реестра."""
    if not keys:
        return
    async with write_scope() as s:
        await s.execute(sa_delete(InterfaceSetting).where(InterfaceSetting.key.in_(keys)))


async def delete_all() -> None:
    async with write_scope() as s:
        await s.execute(sa_delete(InterfaceSetting))


async def prune_unknown(known_keys: Sequence[str]) -> int:
    """Убрать строки с ключами вне реестра; вернуть их число, чтобы старт сказал об этом в лог.

    Настройка, снятая с производства вместе с версией фронта, иначе осталась бы в базе навсегда.
    """
    async with write_scope() as s:
        result = await s.execute(
            sa_delete(InterfaceSetting).where(InterfaceSetting.key.not_in(known_keys))
        )
        return result.rowcount or 0


__all__ = ["list_all", "upsert_many", "delete_many", "delete_all", "prune_unknown"]
