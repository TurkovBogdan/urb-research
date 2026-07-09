"""SettingsRegistry: schema validation, load/update/reset, on_settings_change."""

from __future__ import annotations

from typing import Any

import pytest

from src.core.settings.fields import ChoiceField, IntField
from src.core.settings.registry import SettingsRegistry, get_registry
from src.core.config import Config
from src.core.crud import module_settings as crud
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.core.module import Module


@pytest.fixture
async def db():
    engine = await init_database(Config())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


class _M(Module):
    name = "m"
    settings_schema = (
        IntField(key="n", label="N", default_=5, min=0, max=100),
        ChoiceField(
            key="mode", label="Mode", default_="a",
            options={"a": "A", "b": "B"},
        ),
    )

    def __init__(self) -> None:
        self.calls: list[Any] = []

    def on_settings_change(self, store: Any) -> None:
        self.calls.append(store)


@pytest.mark.pure
def test_register_schema_validates_fail_fast():
    class Bad(Module):
        name = "bad"
        settings_schema = (IntField(key="n", label="N", default_=200, max=100),)

    reg = SettingsRegistry()
    with pytest.raises(ValueError):
        reg.register_schema(Bad())


@pytest.mark.pure
def test_get_before_load_initial_raises():
    reg = SettingsRegistry()
    m = _M()
    reg.register_schema(m)
    with pytest.raises(RuntimeError):
        reg.get("m")


@pytest.mark.db
async def test_load_initial_seeds_defaults_and_calls_hook(db):
    reg = get_registry()
    m = _M()
    reg.register_schema(m)
    await reg.load_initial("m")
    store = reg.get("m")
    assert store.n == 5
    assert store.mode == "a"
    assert len(m.calls) == 1


@pytest.mark.db
async def test_update_validates_persists_and_dispatches(db):
    reg = get_registry()
    m = _M()
    reg.register_schema(m)
    await reg.load_initial("m")
    m.calls.clear()

    new_store = await reg.update("m", "n", 42)
    assert new_store.n == 42
    assert reg.get("m").n == 42
    assert len(m.calls) == 1

    row = await crud.get_one("m", "n")
    assert row is not None and row.value == "42"


@pytest.mark.db
async def test_update_invalid_value_raises_and_no_swap(db):
    reg = get_registry()
    m = _M()
    reg.register_schema(m)
    await reg.load_initial("m")
    old_store = reg.get("m")

    with pytest.raises(ValueError):
        await reg.update("m", "n", 999)  # out of max
    assert reg.get("m") is old_store


@pytest.mark.db
async def test_reset_writes_default_and_dispatches(db):
    reg = get_registry()
    m = _M()
    reg.register_schema(m)
    await reg.load_initial("m")
    await reg.update("m", "n", 42)
    m.calls.clear()

    new_store = await reg.reset("m", "n")
    assert new_store.n == 5
    row = await crud.get_one("m", "n")
    assert row is not None and row.value == "5"
    assert len(m.calls) == 1


@pytest.mark.db
async def test_corrupt_db_row_falls_back_to_default(db):
    reg = get_registry()
    m = _M()
    reg.register_schema(m)
    # Подсадим невалидное значение в БД ДО первой загрузки.
    await crud.upsert("m", "n", "not-an-int")
    await reg.load_initial("m")
    store = reg.get("m")
    assert store.n == 5  # default
    # Корректное значение должно быть перезаписано в БД.
    row = await crud.get_one("m", "n")
    assert row is not None and row.value == "5"


@pytest.mark.db
async def test_orphan_db_row_is_ignored(db):
    reg = get_registry()
    m = _M()
    reg.register_schema(m)
    await reg.load_initial("m")
    # Добавим ключ, которого нет в схеме.
    await crud.upsert("m", "stale_key", "1")
    # _reload не должен упасть.
    await reg.update("m", "n", 7)
    assert reg.get("m").n == 7
    # Orphan-ключ остаётся в БД.
    row = await crud.get_one("m", "stale_key")
    assert row is not None


@pytest.mark.db
async def test_on_settings_change_exception_does_not_break_update(db):
    class Boom(Module):
        name = "boom"
        settings_schema = (IntField(key="n", label="N", default_=1),)

        def on_settings_change(self, store: Any) -> None:
            raise RuntimeError("boom")

    reg = get_registry()
    reg.register_schema(Boom())
    await reg.load_initial("boom")
    new_store = await reg.update("boom", "n", 42)
    assert new_store.n == 42
    assert reg.get("boom").n == 42
