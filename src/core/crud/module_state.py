"""CRUD для core_modules_state. Каждая функция открывает session_scope сама.

Произвольное состояние модуля по ключу (module, code). Зеркало
``crud/module_settings.py``, но value — JSONB (структура, а не typed-string).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import session_scope
from src.core.models.module_state import CoreModuleState
from src.core.utils.date import utc_now


def _insert_for(session: AsyncSession):
    dialect = session.bind.dialect.name if session.bind else "postgresql"
    if dialect == "sqlite":
        return sqlite_insert
    return pg_insert


async def list_for_module(module: str) -> list[CoreModuleState]:
    async with session_scope() as s:
        rows = (
            await s.execute(
                select(CoreModuleState).where(CoreModuleState.module == module)
            )
        ).scalars().all()
        return list(rows)


async def get_one(module: str, code: str) -> CoreModuleState | None:
    async with session_scope() as s:
        return (
            await s.execute(
                select(CoreModuleState).where(
                    CoreModuleState.module == module,
                    CoreModuleState.code == code,
                )
            )
        ).scalar_one_or_none()


async def get_value(module: str, code: str) -> Any | None:
    row = await get_one(module, code)
    return row.value if row is not None else None


async def upsert(module: str, code: str, value: Any) -> None:
    """INSERT … ON CONFLICT DO UPDATE: обновляет value+updated_at, created_at — только при первом INSERT."""
    async with session_scope() as s:
        insert = _insert_for(s)
        now = utc_now()
        stmt = insert(CoreModuleState).values(
            module=module,
            code=code,
            value=value,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["module", "code"],
            set_={"value": stmt.excluded.value, "updated_at": now},
        )
        await s.execute(stmt)


async def seed_if_absent(module: str, code: str, value: Any) -> bool:
    """INSERT … ON CONFLICT DO NOTHING. Возвращает True, если строка создана."""
    async with session_scope() as s:
        insert = _insert_for(s)
        now = utc_now()
        stmt = (
            insert(CoreModuleState)
            .values(
                module=module,
                code=code,
                value=value,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=["module", "code"])
            .returning(CoreModuleState.module)
        )
        result = await s.execute(stmt)
        return result.scalar_one_or_none() is not None


async def delete(module: str, code: str) -> None:
    async with session_scope() as s:
        await s.execute(
            sa_delete(CoreModuleState).where(
                CoreModuleState.module == module,
                CoreModuleState.code == code,
            )
        )


async def delete_for_module(module: str) -> None:
    async with session_scope() as s:
        await s.execute(
            sa_delete(CoreModuleState).where(CoreModuleState.module == module)
        )


async def list_all() -> list[CoreModuleState]:
    async with session_scope() as s:
        rows = (await s.execute(select(CoreModuleState))).scalars().all()
        return list(rows)


__all__ = [
    "list_for_module",
    "get_one",
    "get_value",
    "upsert",
    "seed_if_absent",
    "delete",
    "delete_for_module",
    "list_all",
]
