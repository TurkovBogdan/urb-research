"""Распределённые локи: ORM-строка ``CoreLockRow``, CRUD-операции, ``CoreLock``.

Один файл, потому что все три слоя — про одну сущность и не используются
по отдельности нигде, кроме как друг другом.

Публичное:
- ``CoreLockRow`` — ORM-модель таблицы ``core_locks`` (для select-ов в коде).
- ``CoreLock`` — высокоуровневая обёртка: ``acquire`` / ``release`` / ``extend``.
- ``release_for_owners(owners)`` — bulk-cleanup, используется
  раннером и тикером для авто-снятия локов завершённых/zombie задач.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import String, delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from src.core.database import session_scope
from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now


# ── ORM ─────────────────────────────────────────────────────────────────────

class CoreLockRow(Base):
    """Строка таблицы ``core_locks`` — один активный лок на ``key``."""

    __tablename__ = "core_locks"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner: Mapped[str] = mapped_column(String(128), index=True)
    acquired_at: Mapped[datetime] = mapped_column(timestamp())
    expires_at: Mapped[datetime] = mapped_column(timestamp(), index=True)


# ── CRUD ────────────────────────────────────────────────────────────────────

def _insert_for(session: AsyncSession):
    dialect = session.bind.dialect.name if session.bind else "postgresql"
    return sqlite_insert if dialect == "sqlite" else pg_insert


async def _acquire(
    session: AsyncSession, *, key: str, owner: str, ttl_seconds: int
) -> bool:
    """INSERT либо перехватить протухший лок. True = строка теперь наша."""
    insert = _insert_for(session)
    now = utc_now()
    expires = now + timedelta(seconds=ttl_seconds)
    stmt = insert(CoreLockRow).values(
        key=key, owner=owner, acquired_at=now, expires_at=expires
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["key"],
        set_={
            "owner": stmt.excluded.owner,
            "acquired_at": stmt.excluded.acquired_at,
            "expires_at": stmt.excluded.expires_at,
        },
        where=(CoreLockRow.expires_at < stmt.excluded.acquired_at),
    ).returning(CoreLockRow.owner)
    result = await session.execute(stmt)
    row = result.first()
    return row is not None and row[0] == owner


async def _release(
    session: AsyncSession, *, key: str, owner: str
) -> bool:
    """DELETE WHERE key=? AND owner=?. True = реально удалили."""
    result = await session.execute(
        delete(CoreLockRow).where(
            CoreLockRow.key == key, CoreLockRow.owner == owner
        )
    )
    return result.rowcount > 0


async def _is_owner(
    session: AsyncSession, *, key: str, owner: str
) -> bool:
    """True, если лок существует И принадлежит ``owner``."""
    stmt = select(CoreLockRow.owner).where(CoreLockRow.key == key)
    current = (await session.execute(stmt)).scalar_one_or_none()
    return current == owner


async def _extend(
    session: AsyncSession, *, key: str, owner: str, ttl_seconds: int
) -> bool:
    """Продлить TTL, если мы всё ещё владелец. False — потеряли лок."""
    expires = utc_now() + timedelta(seconds=ttl_seconds)
    stmt = (
        update(CoreLockRow)
        .where(CoreLockRow.key == key, CoreLockRow.owner == owner)
        .values(expires_at=expires)
    )
    result = await session.execute(stmt)
    return result.rowcount > 0


async def release_for_owners(owners: list[str]) -> None:
    """DELETE WHERE owner IN (...). Bulk cleanup для zombie-уборки задач."""
    if not owners:
        return
    async with session_scope() as s:
        await s.execute(
            delete(CoreLockRow).where(CoreLockRow.owner.in_(owners))
        )


# ── Высокоуровневый ``CoreLock`` ────────────────────────────────────────────

class CoreLock:
    """Удерживаемый распределённый лок. Создаётся через ``CoreLock.acquire``."""

    def __init__(self, key: str, owner: str) -> None:
        self.key = key
        self.owner = owner

    @classmethod
    async def acquire(
        cls, key: str, ttl: int, *, owner: str | None = None
    ) -> "CoreLock | None":
        """Поставить лок. ``CoreLock`` если взяли, иначе ``None``.

        ``ttl`` — TTL в секундах. ``owner`` опциональный: если не передан —
        генерируется ULID (анонимный одноразовый владелец).
        """
        if owner is None:
            owner = str(ULID())
        async with session_scope() as s:
            ok = await _acquire(s, key=key, owner=owner, ttl_seconds=ttl)
        return cls(key, owner) if ok else None

    async def release(self) -> bool:
        """Снять лок. True = реально сняли (мы ещё были владельцем)."""
        async with session_scope() as s:
            return await _release(s, key=self.key, owner=self.owner)

    async def is_owner(self) -> bool:
        """Fencing-проверка: лок всё ещё на нас, или нас перехватили?"""
        async with session_scope() as s:
            return await _is_owner(s, key=self.key, owner=self.owner)

    async def extend(self, ttl: int) -> bool:
        """Продлить TTL (секунды). Сначала проверяем владение, потом UPDATE."""
        if not await self.is_owner():
            return False
        async with session_scope() as s:
            return await _extend(
                s, key=self.key, owner=self.owner, ttl_seconds=ttl
            )

    @classmethod
    async def force_release(cls, key: str) -> bool:
        """Снять лок по ключу без проверки владельца. True = реально сняли."""
        async with session_scope() as s:
            result = await s.execute(
                delete(CoreLockRow).where(CoreLockRow.key == key)
            )
            return result.rowcount > 0


__all__ = ["CoreLock", "CoreLockRow", "release_for_owners"]
