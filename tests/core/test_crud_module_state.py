"""``crud.module_state`` + ``module_store`` аксессор: round-trip произвольного состояния."""

from __future__ import annotations

import pytest

from src.core.config import Config
from src.core.crud import module_state as crud
from src.core.database import close_database, init_database
from src.core.module import Module
from src.core.module_state import module_store


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    from src.core.database.runtime import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.mark.db
async def test_upsert_inserts_then_updates(db):
    await crud.upsert("m", "cursor", {"history_id": "1"})
    first = await crud.get_one("m", "cursor")
    assert first is not None
    assert first.value == {"history_id": "1"}
    created = first.created_at

    await crud.upsert("m", "cursor", {"history_id": "2"})
    second = await crud.get_one("m", "cursor")
    assert second.value == {"history_id": "2"}
    assert second.created_at == created          # created_at заморожен
    assert second.updated_at >= second.created_at


@pytest.mark.db
async def test_get_misses_return_none(db):
    assert await crud.get_one("m", "absent") is None
    assert await crud.get_value("m", "absent") is None


@pytest.mark.db
async def test_seed_if_absent_only_first_wins(db):
    assert await crud.seed_if_absent("m", "k", {"v": 1}) is True
    assert await crud.seed_if_absent("m", "k", {"v": 2}) is False
    assert await crud.get_value("m", "k") == {"v": 1}     # повторный seed не перезаписал


@pytest.mark.db
async def test_jsonb_roundtrips_nested_structure(db):
    payload = {
        "nested": {"a": [1, 2, 3], "b": True},
        "n": 4,
        "flag": False,
        "empty": None,
        "items": ["x", {"y": 1}],
    }
    await crud.upsert("m", "blob", payload)
    assert await crud.get_value("m", "blob") == payload   # не строка, структура цела


@pytest.mark.db
async def test_composite_key_isolates_modules(db):
    await crud.upsert("a", "k", {"who": "a"})
    await crud.upsert("b", "k", {"who": "b"})
    assert await crud.get_value("a", "k") == {"who": "a"}
    assert await crud.get_value("b", "k") == {"who": "b"}


@pytest.mark.db
async def test_delete_and_delete_for_module(db):
    await crud.upsert("m", "k1", 1)
    await crud.upsert("m", "k2", 2)
    await crud.upsert("other", "k", 9)

    await crud.delete("m", "k1")
    assert await crud.get_one("m", "k1") is None
    assert await crud.get_value("m", "k2") == 2

    await crud.delete_for_module("m")
    assert await crud.list_for_module("m") == []
    assert await crud.get_value("other", "k") == 9       # чужой namespace не тронут


@pytest.mark.db
async def test_accessor_set_get_all(db):
    store = module_store("demo_module")
    await store.set("import_cursor", {"history_id": "98213"})

    assert await store.get("import_cursor") == {"history_id": "98213"}
    assert await store.get("missing") is None
    assert await store.get("missing", default={}) == {}

    await store.set("counter", 7)
    assert await store.all() == {"import_cursor": {"history_id": "98213"}, "counter": 7}


@pytest.mark.db
async def test_accessor_seed_and_delete(db):
    store = module_store("m")
    assert await store.seed_if_absent("k", "first") is True
    assert await store.seed_if_absent("k", "second") is False
    assert await store.get("k") == "first"

    await store.delete("k")
    assert await store.get("k") is None


@pytest.mark.db
async def test_module_store_property_binds_name(db):
    class _Demo(Module):
        name = "demo_mod"

    await _Demo().store.set("k", {"ok": True})
    assert await module_store("demo_mod").get("k") == {"ok": True}


@pytest.mark.db
async def test_list_all_spans_modules(db):
    await crud.upsert("a", "k1", 1)
    await crud.upsert("a", "k2", 2)
    await crud.upsert("b", "k", 3)

    rows = {(r.module, r.code): r.value for r in await crud.list_all()}
    assert rows == {("a", "k1"): 1, ("a", "k2"): 2, ("b", "k"): 3}


class _FakeBind:
    def __init__(self, dialect_name: str):
        self.dialect = type("D", (), {"name": dialect_name})()


class _FakeSession:
    def __init__(self, dialect_name: str | None):
        self.bind = _FakeBind(dialect_name) if dialect_name else None


@pytest.mark.pure
def test_insert_for_picks_dialect():
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    assert crud._insert_for(_FakeSession("sqlite")) is sqlite_insert
    assert crud._insert_for(_FakeSession("postgresql")) is pg_insert
    assert crud._insert_for(_FakeSession(None)) is pg_insert    # bind=None → postgres default
