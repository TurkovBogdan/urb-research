"""CRUD для core_modules_settings. Каждая функция открывает session_scope сама."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import session_scope
from src.core.models.module_settings import CoreModuleSetting
from src.core.utils.date import utc_now


def _insert_for(session: AsyncSession):
    dialect = session.bind.dialect.name if session.bind else "postgresql"
    if dialect == "sqlite":
        return sqlite_insert
    return pg_insert


async def list_for_module(module: str) -> list[CoreModuleSetting]:
    async with session_scope() as s:
        rows = (
            await s.execute(
                select(CoreModuleSetting).where(CoreModuleSetting.module == module)
            )
        ).scalars().all()
        return list(rows)


async def get_one(module: str, key: str) -> CoreModuleSetting | None:
    async with session_scope() as s:
        return (
            await s.execute(
                select(CoreModuleSetting).where(
                    CoreModuleSetting.module == module,
                    CoreModuleSetting.key == key,
                )
            )
        ).scalar_one_or_none()


async def upsert(module: str, key: str, value: str) -> None:
    """INSERT … ON CONFLICT DO UPDATE: обновляет value+updated_at, created_at — только при первом INSERT."""
    async with session_scope() as s:
        insert = _insert_for(s)
        now = utc_now()
        stmt = insert(CoreModuleSetting).values(
            module=module,
            key=key,
            value=value,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["module", "key"],
            set_={"value": stmt.excluded.value, "updated_at": now},
        )
        await s.execute(stmt)


async def seed_if_absent(module: str, key: str, value: str) -> bool:
    """INSERT … ON CONFLICT DO NOTHING. Возвращает True, если строка создана."""
    async with session_scope() as s:
        insert = _insert_for(s)
        now = utc_now()
        stmt = (
            insert(CoreModuleSetting)
            .values(
                module=module,
                key=key,
                value=value,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=["module", "key"])
            .returning(CoreModuleSetting.module)
        )
        result = await s.execute(stmt)
        return result.scalar_one_or_none() is not None


async def delete(module: str, key: str) -> None:
    async with session_scope() as s:
        await s.execute(
            sa_delete(CoreModuleSetting).where(
                CoreModuleSetting.module == module,
                CoreModuleSetting.key == key,
            )
        )


async def list_all() -> list[CoreModuleSetting]:
    async with session_scope() as s:
        rows = (await s.execute(select(CoreModuleSetting))).scalars().all()
        return list(rows)


__all__ = [
    "list_for_module",
    "get_one",
    "upsert",
    "seed_if_absent",
    "delete",
    "list_all",
]
