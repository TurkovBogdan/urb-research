"""CRUD core_modules_settings: seed_if_absent, upsert."""

from __future__ import annotations

import asyncio

import pytest

from src.core.config import Config
from src.core.crud import module_settings as crud
from src.core.database import close_database, init_database
from src.core.database.runtime import Base



@pytest.fixture
async def db():
    engine = await init_database(Config())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.mark.db
async def test_seed_if_absent_is_idempotent(db):
    assert await crud.seed_if_absent("m", "k", "1") is True
    row1 = await crud.get_one("m", "k")
    assert row1 is not None
    created_at1 = row1.created_at

    assert await crud.seed_if_absent("m", "k", "2") is False
    row2 = await crud.get_one("m", "k")
    assert row2 is not None
    assert row2.created_at == created_at1
    assert row2.value == "1"  # not overwritten


@pytest.mark.db
async def test_upsert_preserves_created_at_updates_updated_at(db):
    await crud.seed_if_absent("m", "k", "1")
    row1 = await crud.get_one("m", "k")
    assert row1 is not None
    created_at1 = row1.created_at
    updated_at1 = row1.updated_at

    await asyncio.sleep(1.1)  # TIMESTAMP precision=0 — секундная гранулярность
    await crud.upsert("m", "k", "2")

    row2 = await crud.get_one("m", "k")
    assert row2 is not None
    assert row2.value == "2"
    assert row2.created_at == created_at1
    assert row2.updated_at > updated_at1


@pytest.mark.db
async def test_list_for_module_filters_by_module(db):
    await crud.seed_if_absent("a", "k1", "1")
    await crud.seed_if_absent("a", "k2", "2")
    await crud.seed_if_absent("b", "k1", "9")
    rows = await crud.list_for_module("a")
    assert {r.key for r in rows} == {"k1", "k2"}
