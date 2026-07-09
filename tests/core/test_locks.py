"""Тесты core.locks: CRUD + CoreLock.

CRUD-уровень — детерминированная семантика owner-based локов.
CoreLock — статический ``acquire`` создаёт объект, методы делают release/extend.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from src.core.config import Config
from src.core.database import close_database, init_database, session_scope
from src.core.locks import CoreLock, CoreLockRow, release_for_owners
from src.core.locks.lock import _acquire, _extend, _is_owner, _release



@pytest.fixture
async def db(config: Config):
    """Инициализирует engine и создаёт core-таблицы."""
    engine = await init_database(config)
    from src.core.database.runtime import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


# ── CRUD-уровень ────────────────────────────────────────────────────────────


@pytest.mark.db
async def test_crud_acquire_free(db):
    async with session_scope() as s:
        ok = await _acquire(s, key="k1", owner="o1", ttl_seconds=60)
    assert ok is True


@pytest.mark.db
async def test_crud_acquire_busy_returns_false(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=60)
    async with session_scope() as s:
        ok = await _acquire(s, key="k", owner="o2", ttl_seconds=60)
    assert ok is False


@pytest.mark.db
async def test_crud_acquire_expired_is_taken_over(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=-1)
    async with session_scope() as s:
        ok = await _acquire(s, key="k", owner="o2", ttl_seconds=60)
    assert ok is True
    async with session_scope() as s:
        row = (await s.execute(select(CoreLockRow).where(CoreLockRow.key == "k"))).scalar_one()
    assert row.owner == "o2"


@pytest.mark.db
async def test_crud_release_by_owner_deletes_row(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=60)
    async with session_scope() as s:
        ok = await _release(s, key="k", owner="o1")
    assert ok is True
    async with session_scope() as s:
        row = (await s.execute(select(CoreLockRow).where(CoreLockRow.key == "k"))).scalar_one_or_none()
    assert row is None


@pytest.mark.db
async def test_crud_release_wrong_owner_no_op(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=60)
    async with session_scope() as s:
        ok = await _release(s, key="k", owner="o2")
    assert ok is False
    async with session_scope() as s:
        row = (await s.execute(select(CoreLockRow).where(CoreLockRow.key == "k"))).scalar_one()
    assert row.owner == "o1"


@pytest.mark.db
async def test_crud_is_owner_true_for_current_false_for_other(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=60)
    async with session_scope() as s:
        assert await _is_owner(s, key="k", owner="o1") is True
        assert await _is_owner(s, key="k", owner="o2") is False
        assert await _is_owner(s, key="missing", owner="o1") is False


@pytest.mark.db
async def test_crud_is_owner_after_takeover_returns_false(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=-1)
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o2", ttl_seconds=60)
    async with session_scope() as s:
        assert await _is_owner(s, key="k", owner="o1") is False
        assert await _is_owner(s, key="k", owner="o2") is True


@pytest.mark.db
async def test_crud_extend_only_for_owner(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o1", ttl_seconds=60)
    async with session_scope() as s:
        assert await _extend(s, key="k", owner="o2", ttl_seconds=60) is False
        assert await _extend(s, key="k", owner="o1", ttl_seconds=60) is True


@pytest.mark.db
async def test_crud_release_for_owners_bulk(db):
    async with session_scope() as s:
        await _acquire(s, key="k1", owner="task_run:1", ttl_seconds=60)
        await _acquire(s, key="k2", owner="task_run:2", ttl_seconds=60)
        await _acquire(s, key="k3", owner="task_run:3", ttl_seconds=60)
    await release_for_owners(["task_run:1", "task_run:3"])
    async with session_scope() as s:
        rows = (await s.execute(select(CoreLockRow))).scalars().all()
    assert {r.key for r in rows} == {"k2"}


@pytest.mark.db
async def test_crud_release_for_owners_empty_list_noop(db):
    async with session_scope() as s:
        await _acquire(s, key="k", owner="o", ttl_seconds=60)
    await release_for_owners([])
    async with session_scope() as s:
        rows = (await s.execute(select(CoreLockRow))).scalars().all()
    assert len(rows) == 1


# ── Lock-модель ─────────────────────────────────────────────────────────────


@pytest.mark.db
async def test_lock_acquire_returns_instance(db):
    lock = await CoreLock.acquire("k", 60, owner="o")
    assert isinstance(lock, CoreLock)
    assert lock.key == "k"
    assert lock.owner == "o"


@pytest.mark.db
async def test_lock_acquire_busy_returns_none(db):
    first = await CoreLock.acquire("k", 60, owner="a")
    assert first is not None
    second = await CoreLock.acquire("k", 60, owner="b")
    assert second is None


@pytest.mark.db
async def test_lock_release_removes_row(db):
    lock = await CoreLock.acquire("k", 60, owner="o")
    assert lock is not None
    assert await lock.release() is True
    assert await lock.is_owner() is False


@pytest.mark.db
async def test_lock_release_after_takeover_returns_false(db):
    """Если протух и кто-то перехватил — release нашего Lock-а ничего не сносит."""
    lock_a = await CoreLock.acquire("k", -1, owner="a")
    assert lock_a is not None
    lock_b = await CoreLock.acquire("k", 60, owner="b")
    assert lock_b is not None
    assert await lock_a.is_owner() is False
    assert await lock_a.release() is False
    assert await lock_b.is_owner() is True


@pytest.mark.db
async def test_lock_extend_keeps_ownership(db):
    lock = await CoreLock.acquire("k", 60, owner="a")
    assert lock is not None
    assert await lock.extend(120) is True


@pytest.mark.db
async def test_lock_acquire_without_owner_generates_ulid(db):
    """Если owner не передан — генерируется уникальный ULID."""
    lock_a = await CoreLock.acquire("ka", 60)
    lock_b = await CoreLock.acquire("kb", 60)
    assert lock_a is not None and lock_b is not None
    # 26-символьный Crockford base32 — формат ULID
    assert len(lock_a.owner) == 26
    assert lock_a.owner != lock_b.owner
