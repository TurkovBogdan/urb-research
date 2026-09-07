"""core_interface: подъём модуля — самопроверка реестра и уборка снятых с производства ключей."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from src.modules.core_interface import crud
from src.modules.core_interface.module import CoreInterfaceModule

pytestmark = pytest.mark.db


async def test_startup_prunes_keys_outside_the_registry(db):
    await crud.upsert_many({"interface_theme": "light", "app_message_mode": "html"})

    await CoreInterfaceModule().on_startup(FastAPI())

    assert await crud.list_all() == {"interface_theme": "light"}


async def test_startup_leaves_an_empty_table_alone(db):
    await CoreInterfaceModule().on_startup(FastAPI())

    assert await crud.list_all() == {}
