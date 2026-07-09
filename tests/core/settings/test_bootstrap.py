"""Bootstrap: register_settings_schemas + load_initial_stores."""

from __future__ import annotations

from typing import Any

import pytest

from src.core.settings.bootstrap import (
    load_initial_stores,
    register_settings_schemas,
)
from src.core.settings.fields import IntField
from src.core.settings.registry import get_registry
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
    name = "boot_m"
    settings_schema = (IntField(key="n", label="N", default_=10),)

    def __init__(self) -> None:
        self.calls: list[Any] = []

    def on_settings_change(self, store: Any) -> None:
        self.calls.append(store)


class _NoSettings(Module):
    name = "nope"


@pytest.mark.db
async def test_first_boot_seeds_defaults(db):
    register_settings_schemas([_M()])
    await load_initial_stores([_M()])
    row = await crud.get_one("boot_m", "n")
    assert row is not None and row.value == "10"


@pytest.mark.db
async def test_second_boot_keeps_user_value(db):
    m = _M()
    register_settings_schemas([m])
    await load_initial_stores([m])
    await get_registry().update("boot_m", "n", 99)

    # Эмулируем перезапуск: реестр чистим, но БД остаётся.
    get_registry().clear()
    m2 = _M()
    register_settings_schemas([m2])
    await load_initial_stores([m2])
    assert get_registry().get("boot_m").n == 99


@pytest.mark.db
async def test_module_without_schema_is_skipped(db):
    register_settings_schemas([_NoSettings()])
    await load_initial_stores([_NoSettings()])
    assert get_registry().modules() == []
