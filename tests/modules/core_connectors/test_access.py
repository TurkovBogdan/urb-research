"""core_connectors: записи доступа — запись, статусы, шифрование в строке, фасад.

Проверяем то, ради чего заводилась таблица: значения правятся в runtime и видны следующему
вызову, секрет не затирается пустой формой, статус считается без сети, а отказ приходит
типизированным — «не настроено» отличимо от «выключено» и от «не расшифровывается».
"""

from __future__ import annotations

import base64
import os

import pytest

from src.modules.core_connectors import service
from src.modules.core_connectors.access import crud, crypto
from src.modules.core_connectors.access.model import (
    ACCESS_STATUS_DISABLED,
    ACCESS_STATUS_OK,
    ACCESS_STATUS_UNCONFIGURED,
    ACCESS_STATUS_UNDECRYPTABLE,
)
from src.modules.core_connectors.access.store import access_store
from src.modules.core_connectors.connectors.tavily import TavilyConnector
from src.modules.core_connectors.errors import (
    AccessNotConfigured,
    ConnectorDisabled,
    UnknownConnector,
)

pytestmark = pytest.mark.db


async def test_created_record_is_ready_and_opens_a_connector(db):
    await service.create_access(connector="tavily", values={"api_key": "sk-1"})

    connector = await service.open_connector("tavily")

    assert isinstance(connector, TavilyConnector)
    assert connector.access.require("api_key") == "sk-1"


async def test_unknown_connector_is_named_as_such(db):
    with pytest.raises(UnknownConnector):
        await service.open_connector("nope")


async def test_missing_record_is_not_configured_rather_than_a_service_failure(db):
    with pytest.raises(AccessNotConfigured):
        await service.open_connector("tavily")


async def test_empty_required_field_keeps_the_record_unconfigured(db):
    row = await service.create_access(connector="tavily", values={})

    assert row.status.status == ACCESS_STATUS_UNCONFIGURED
    with pytest.raises(AccessNotConfigured):
        await service.open_connector("tavily")


async def test_disabled_record_refuses_with_its_own_reason(db):
    await service.create_access(connector="tavily", values={"api_key": "sk-1"}, enabled=False)

    with pytest.raises(ConnectorDisabled):
        await service.open_connector("tavily")


async def test_status_of_a_disabled_record_is_disabled(db):
    row = await service.create_access(
        connector="tavily", values={"api_key": "sk-1"}, enabled=False
    )

    assert row.status.status == ACCESS_STATUS_DISABLED


async def test_new_key_is_visible_to_the_next_call_without_a_restart(db):
    row = await service.create_access(connector="tavily", values={"api_key": "old"})
    assert (await service.open_connector("tavily")).access.require("api_key") == "old"

    await service.update_access(row.id, values={"api_key": "new"})

    assert (await service.open_connector("tavily")).access.require("api_key") == "new"


async def test_blank_secret_means_untouched_not_erased(db):
    row = await service.create_access(connector="tavily", values={"api_key": "keep-me"})

    await service.update_access(row.id, values={"api_key": ""})

    assert (await service.open_connector("tavily")).access.require("api_key") == "keep-me"


async def test_sentinel_secret_means_untouched(db):
    row = await service.create_access(connector="tavily", values={"api_key": "keep-me"})

    await service.update_access(row.id, values={"api_key": service.SECRET_UNCHANGED})

    assert (await service.open_connector("tavily")).access.require("api_key") == "keep-me"


async def test_clearing_is_explicit(db):
    row = await service.create_access(connector="tavily", values={"api_key": "drop-me"})

    updated = await service.update_access(row.id, clear=["api_key"])

    assert updated.status.status == ACCESS_STATUS_UNCONFIGURED


async def test_unknown_field_is_dropped_rather_than_stored(db):
    row = await service.create_access(
        connector="tavily", values={"api_key": "sk-1", "typo_key": "junk"}
    )

    stored = await crud.access_get(row.id)

    assert set(stored.values) == {"api_key"}


async def test_detail_never_returns_the_secret(db):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-secret"})

    detail = await service.access_detail(row.id)

    assert detail.values["api_key"] == service.SECRET_UNCHANGED
    assert "sk-secret" not in str(detail.model_dump())
    assert [f["key"] for f in detail.fields] == ["api_key"]
    assert detail.fields[0]["is_set"] is True


async def test_non_secret_field_is_returned_as_is(db):
    row = await service.create_access(
        connector="web_scrapper", values={"base_url": "http://127.0.0.1:19020"}
    )

    detail = await service.access_detail(row.id)

    assert detail.values["base_url"] == "http://127.0.0.1:19020"


async def test_daemon_without_a_token_is_a_legitimate_configuration(db):
    # У локального демона авторизация может быть выключена — обязательных полей нет
    row = await service.create_access(connector="web_scrapper", values={})

    assert row.status.status == ACCESS_STATUS_OK


async def test_secret_is_encrypted_in_the_row(db, master_key):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-secret"})

    stored = await crud.access_get(row.id)

    assert stored.values["api_key"].startswith("v1.")
    assert "sk-secret" not in stored.values["api_key"]
    assert stored.data_key and stored.key_version
    assert (await service.open_connector("tavily")).access.require("api_key") == "sk-secret"


async def test_record_without_the_master_key_gets_a_status_not_a_crash(db, master_key, monkeypatch):

    row = await service.create_access(connector="tavily", values={"api_key": "sk-secret"})
    access_store.clear()

    monkeypatch.setattr(crypto, "configured_master_key", lambda: "")  # как чужая копия базы

    rows = await service.access_rows()

    assert rows[0].status.status == ACCESS_STATUS_UNDECRYPTABLE
    assert rows[0].status.detail  # причина названа, страница живёт


async def test_encryption_switched_on_later_seals_the_next_write(db, monkeypatch):

    row = await service.create_access(connector="tavily", values={"api_key": "plain"})
    stored = await crud.access_get(row.id)
    assert stored.values["api_key"] == "plain"  # ключа не было — законный открытый текст

    key = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    monkeypatch.setattr(crypto, "configured_master_key", lambda: key)
    await service.update_access(row.id, values={"api_key": "sealed"})

    stored = await crud.access_get(row.id)
    assert stored.values["api_key"].startswith("v1.")
    assert (await service.open_connector("tavily")).access.require("api_key") == "sealed"


async def test_a_key_that_appeared_later_seals_the_records_that_were_open(db, monkeypatch):

    row = await service.create_access(connector="tavily", values={"api_key": "plain"})
    await service.create_access(connector="web_scrapper", values={"base_url": "http://x"})
    assert (await crud.access_get(row.id)).values["api_key"] == "plain"

    key = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    monkeypatch.setattr(crypto, "configured_master_key", lambda: key)
    sealed = await service.seal_plaintext_secrets()

    assert sealed == [row.id]  # несекретный base_url трогать незачем
    assert (await crud.access_get(row.id)).values["api_key"].startswith("v1.")
    assert (await service.open_connector("tavily")).access.require("api_key") == "plain"
    assert await service.seal_plaintext_secrets() == []  # повтор ничего не делает


async def test_sealing_does_nothing_without_a_key(db):
    await service.create_access(connector="tavily", values={"api_key": "plain"})

    assert await service.seal_plaintext_secrets() == []


async def test_deleted_record_stops_answering(db):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})

    await service.delete_access(row.id)

    with pytest.raises(AccessNotConfigured):
        await service.open_connector("tavily")


async def test_access_available_answers_without_network(db):
    assert await service.access_available("tavily") is False

    await service.create_access(connector="tavily", values={"api_key": "sk-1"})

    assert await service.access_available("tavily") is True


async def test_a_record_of_another_connector_is_refused(db):
    # Опечатка в id не должна отправить ключ одного вендора другому
    await service.create_access(connector="tavily", values={"api_key": "tavily-key"})
    foreign = await service.create_access(connector="firecrawl", values={"api_key": "fc-key"})

    with pytest.raises(AccessNotConfigured, match="firecrawl"):
        await service.open_connector("tavily", access=foreign.id)


async def test_an_explicit_record_of_the_same_connector_is_taken(db):
    first = await service.create_access(connector="tavily", values={"api_key": "first"})
    second = await service.create_access(connector="tavily", values={"api_key": "second"})

    chosen = await service.open_connector("tavily", access=first.id)

    assert chosen.access.require("api_key") == "first"
    assert second.id != first.id


async def test_only_one_record_stays_default_per_connector(db):
    first = await service.create_access(connector="tavily", values={"api_key": "first"})
    second = await service.create_access(connector="tavily", values={"api_key": "second"})

    rows = {row.id: row for row in await service.access_rows(connector="tavily")}

    assert rows[first.id].is_default is False
    assert rows[second.id].is_default is True
    # Умолчание — то, что отмечено последним, а не то, что раньше по id
    assert (await service.open_connector("tavily")).access.require("api_key") == "second"


async def test_default_of_one_connector_does_not_touch_another(db):
    tavily = await service.create_access(connector="tavily", values={"api_key": "k"})
    await service.create_access(connector="firecrawl", values={"api_key": "k"})

    rows = {row.connector: row for row in await service.access_rows()}

    assert rows["tavily"].id == tavily.id and rows["tavily"].is_default is True


async def test_cache_is_dropped_when_the_record_is_deleted(db):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})
    await service.open_connector("tavily")  # прогреваем кеш значений

    await service.delete_access(row.id)
    fresh = await service.create_access(connector="tavily", values={"api_key": "sk-2"})

    # Идентификатор переиспользуется (sqlite отдаёт max(id)+1) — старое значение из кеша
    # всплыть не должно, иначе новая запись работала бы чужим ключом
    assert fresh.id == row.id
    assert (await service.open_connector("tavily")).access.require("api_key") == "sk-2"


async def test_disabling_a_record_takes_effect_at_once(db):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})
    await service.open_connector("tavily")

    await service.update_access(row.id, enabled=False)

    with pytest.raises(ConnectorDisabled):
        await service.open_connector("tavily")


async def test_values_survive_a_toggle_only_update(db):
    row = await service.create_access(
        connector="web_scrapper", values={"base_url": "http://daemon:19020"}
    )

    await service.update_access(row.id, enabled=False)

    detail = await service.access_detail(row.id)
    assert detail.values["base_url"] == "http://daemon:19020"
    assert detail.enabled is False


async def test_clearing_an_unknown_field_changes_nothing(db):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})

    updated = await service.update_access(row.id, clear=["typo_key"])

    assert updated.status.status == ACCESS_STATUS_OK
