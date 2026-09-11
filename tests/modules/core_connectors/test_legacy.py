"""core_connectors: разовый перенос кредов из старой схемы настроек в записи доступа.

Старые ключи (``tavily_api_key``, ``xai_management_api_key``, тумблеры
``*_gateway_enabled``) лежат строками настроек модуля. Проверяем, что перенос читает их по
паспорту, не повторяется, не трогает старые строки и не создаёт пустых записей.
"""

from __future__ import annotations

import pytest

from src.core.crud import module_settings
from src.core.module_state import module_store
from src.modules.core_connectors import service
from src.modules.core_connectors.access.legacy import (
    LEGACY_IMPORT_MARK,
    import_legacy_accesses,
)

pytestmark = pytest.mark.db


async def _legacy_rows(**values: str) -> None:
    for key, value in values.items():
        await module_settings.upsert("core_connectors", key, value)


async def test_import_creates_one_record_per_connector(db):
    await _legacy_rows(
        tavily_api_key="sk-tavily",
        tavily_gateway_enabled="true",
        xai_api_key="sk-xai",
        xai_management_api_key="sk-xai-mgmt",
        xai_gateway_enabled="false",
    )

    mark = await import_legacy_accesses(module_store("core_connectors"))

    assert set(mark["connectors"]) == {"tavily", "xai"}
    assert (await service.open_connector("tavily")).access.require("api_key") == "sk-tavily"
    rows = {row.connector: row for row in await service.access_rows()}
    assert rows["tavily"].enabled is True
    assert rows["xai"].enabled is False  # выключенный шлюз переехал выключенной записью
    assert rows["xai"].status.status == "disabled"


async def test_management_key_lands_in_its_own_field_of_the_same_connector(db):
    await _legacy_rows(xai_api_key="sk-xai", xai_management_api_key="sk-mgmt")

    await import_legacy_accesses(module_store("core_connectors"))

    values = await service.access_detail((await service.access_rows())[0].id)
    assert set(values.values) == {"api_key", "management_api_key"}  # одна запись, два секрета


async def test_connector_without_any_value_gets_no_record(db):
    await _legacy_rows(tavily_api_key="sk-tavily", firecrawl_api_key="")

    mark = await import_legacy_accesses(module_store("core_connectors"))

    assert mark["connectors"] == ["tavily"]


async def test_connector_with_nothing_to_fill_still_gets_its_record(db):
    # У локального демона авторизация может быть выключена: заполнять нечего, но он
    # работал — признаком служит сама старая строка-тумблер
    await _legacy_rows(web_scrapper_api_key="", web_scrapper_gateway_enabled="true")

    mark = await import_legacy_accesses(module_store("core_connectors"))

    assert mark["connectors"] == ["web_scrapper"]
    assert await service.access_available("web_scrapper") is True


async def test_pasted_whitespace_around_a_token_is_trimmed(db):
    await _legacy_rows(tavily_api_key=" sk-tavily ")

    await import_legacy_accesses(module_store("core_connectors"))

    assert (await service.open_connector("tavily")).access.require("api_key") == "sk-tavily"


async def test_import_runs_once(db):
    await _legacy_rows(tavily_api_key="sk-tavily")
    store = module_store("core_connectors")

    await import_legacy_accesses(store)
    second = await import_legacy_accesses(store)

    assert second is None  # отметка на месте — повтора нет
    assert len(await service.access_rows()) == 1


async def test_old_settings_rows_are_left_in_place(db):
    await _legacy_rows(tavily_api_key="sk-tavily")

    await import_legacy_accesses(module_store("core_connectors"))

    kept = await module_settings.get_one("core_connectors", "tavily_api_key")
    assert kept is not None and kept.value == "sk-tavily"  # страховка до следующего релиза


async def test_import_seeds_from_the_environment_when_settings_are_empty(db, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "sk-from-env")

    mark = await import_legacy_accesses(module_store("core_connectors"))

    assert mark["connectors"] == ["tavily"]
    assert (await service.open_connector("tavily")).access.require("api_key") == "sk-from-env"


async def test_an_existing_record_is_not_duplicated(db):
    # Отметку могли сбросить руками ради повторного переноса — уже заведённое трогать нельзя
    await _legacy_rows(tavily_api_key="sk-legacy")
    await service.create_access(connector="tavily", values={"api_key": "sk-hand-made"})

    mark = await import_legacy_accesses(module_store("core_connectors"))

    assert mark["connectors"] == []
    assert len(await service.access_rows(connector="tavily")) == 1
    assert (await service.open_connector("tavily")).access.require("api_key") == "sk-hand-made"


async def test_nothing_to_import_still_leaves_a_mark(db):
    store = module_store("core_connectors")

    mark = await import_legacy_accesses(store)

    assert mark == {"connectors": []}
    assert await import_legacy_accesses(store) is None  # второй раз не ходит в настройки


async def test_mark_is_stored_in_the_module_state(db):
    await _legacy_rows(tavily_api_key="sk-tavily")
    store = module_store("core_connectors")

    await import_legacy_accesses(store)

    assert await store.get(LEGACY_IMPORT_MARK) == {"connectors": ["tavily"]}
