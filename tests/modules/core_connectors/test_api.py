"""core_connectors: HTTP-поверхность — паспорта, записи, проверка и баланс.

Главное, что здесь проверяется помимо кодов ответа: секрет не уходит наружу ни одним
маршрутом, а живые вызовы отдают диагноз значением, а не пятисоткой.
"""

from __future__ import annotations

import re

import pytest

from src.modules.core_connectors import service

pytestmark = pytest.mark.db

BASE = "/internal"


async def test_connectors_list_returns_passports(client):
    r = await client.get(f"{BASE}/connectors")

    assert r.status_code == 200
    by_service = {p["service"]: p for p in r.json()}
    assert {"tavily", "xai", "web_scrapper"} <= by_service.keys()
    assert by_service["xai"]["owner"] == "core_connectors"
    assert by_service["xai"]["group"] == "models"
    assert [f["key"] for f in by_service["xai"]["fields"]] == ["api_key", "management_api_key"]
    assert by_service["web_scrapper"]["has_balance"] is False


async def test_connector_groups_return_the_reference_in_show_order(client):
    r = await client.get(f"{BASE}/connectors/groups")

    assert r.status_code == 200
    assert [g["code"] for g in r.json()] == ["search", "scraping", "models"]
    assert r.json()[0]["icon"] == "search"  # имя tabler для зеркального реестра фронта


async def test_create_read_update_delete_a_record(client):
    created = await client.post(
        f"{BASE}/accesses", json={"connector": "tavily", "values": {"api_key": "sk-1"}}
    )
    assert created.status_code == 201
    access_id = created.json()["id"]
    assert created.json()["status"]["status"] == "ok"

    detail = await client.get(f"{BASE}/accesses/{access_id}")
    assert detail.json()["values"]["api_key"] == "NOT_CHANGED"  # токен наружу не уходит

    updated = await client.put(f"{BASE}/accesses/{access_id}", json={"enabled": False})
    assert updated.json()["enabled"] is False

    assert (await client.delete(f"{BASE}/accesses/{access_id}")).status_code == 204
    assert (await client.get(f"{BASE}/accesses/{access_id}")).status_code == 404


async def test_unknown_connector_is_rejected_on_create(client):
    r = await client.post(f"{BASE}/accesses", json={"connector": "nope", "values": {}})

    assert r.status_code == 400


async def test_list_carries_status_and_balance_capability(client):
    await service.create_access(connector="tavily", values={"api_key": "sk-1"})
    await service.create_access(connector="web_scrapper", values={})

    r = await client.get(f"{BASE}/accesses")

    by_connector = {row["connector"]: row for row in r.json()}
    assert by_connector["tavily"]["status"]["status"] == "ok"
    assert by_connector["tavily"]["has_balance"] is True
    assert by_connector["web_scrapper"]["has_balance"] is False
    assert by_connector["tavily"]["balance"] is None  # без with_balance в сеть не ходим


async def test_list_filters_by_connector(client):
    await service.create_access(connector="tavily", values={"api_key": "sk-1"})
    await service.create_access(connector="firecrawl", values={"api_key": "sk-2"})

    r = await client.get(f"{BASE}/accesses", params={"connector": "firecrawl"})

    assert [row["connector"] for row in r.json()] == ["firecrawl"]


async def test_check_of_an_unconfigured_record_is_a_diagnosis(client):
    row = await service.create_access(connector="tavily", values={})

    r = await client.post(f"{BASE}/accesses/{row.id}/check")

    assert r.status_code == 200  # неготовая запись — это статус, а не сбой запроса
    assert r.json()["ok"] is False
    assert "api_key" in r.json()["error"]


async def test_balance_of_an_unconfigured_record_is_an_error_value(client):
    row = await service.create_access(connector="tavily", values={})

    r = await client.get(f"{BASE}/accesses/{row.id}/balance")

    assert r.status_code == 200
    assert r.json()["error"]
    assert r.json()["metrics"] == []


async def test_disabling_a_record_shows_up_in_the_list(client):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})

    await client.put(f"{BASE}/accesses/{row.id}", json={"enabled": False})

    listed = (await client.get(f"{BASE}/accesses")).json()[0]
    assert listed["status"]["status"] == "disabled"
    assert listed["status"]["detail"]


async def test_clearing_a_secret_is_explicit_over_http(client):
    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})

    kept = await client.put(f"{BASE}/accesses/{row.id}", json={"values": {"api_key": ""}})
    assert kept.json()["status"]["status"] == "ok"  # пустая строка = «не менял»

    cleared = await client.put(f"{BASE}/accesses/{row.id}", json={"clear": ["api_key"]})
    assert cleared.json()["status"]["status"] == "unconfigured"


async def test_a_broken_master_key_answers_with_a_conflict_not_a_crash(client, monkeypatch):
    from src.modules.core_connectors.access import crypto

    monkeypatch.setattr(crypto, "configured_master_key", lambda: "not-a-key")

    r = await client.post(
        f"{BASE}/accesses", json={"connector": "tavily", "values": {"api_key": "sk-1"}}
    )

    assert r.status_code == 409
    assert "SECRETS_KEY" in r.json()["error"]


async def test_balance_of_a_missing_record_is_not_found_shaped(client):
    r = await client.get(f"{BASE}/accesses/404/balance")

    assert r.status_code == 200  # диагноз значением: карточка рисуется с причиной
    assert r.json()["error"]


async def test_a_too_long_connector_code_is_a_validation_error_not_a_db_failure(client):
    # Колонка — String(64); SQLite длину игнорирует, Postgres упал бы на вставке
    r = await client.post(f"{BASE}/accesses", json={"connector": "t" * 65, "values": {}})

    assert r.status_code == 422


async def test_dates_come_out_as_second_precise_strings(client):
    created = await client.post(f"{BASE}/accesses", json={"connector": "tavily", "values": {}})

    body = created.json()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", body["created_at"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", body["updated_at"])


async def test_detail_of_a_record_whose_connector_is_gone_still_opens(client):
    from src.modules.core_connectors.connectors.registry import connectors_registry
    from src.modules.core_connectors.connectors.tavily import TavilyConnector

    row = await service.create_access(connector="tavily", values={"api_key": "sk-1"})
    connectors_registry.unregister("tavily", owner="core_connectors")
    try:
        r = await client.get(f"{BASE}/accesses/{row.id}")
    finally:
        connectors_registry.register(TavilyConnector, owner="core_connectors")

    assert r.status_code == 200
    assert r.json()["connector_name"] == ""
    assert r.json()["fields"] == []  # паспорта нет — форму строить не из чего
    assert r.json()["status"]["status"] != "ok"


async def test_secret_never_appears_in_any_response(client):
    created = await client.post(
        f"{BASE}/accesses", json={"connector": "tavily", "values": {"api_key": "sk-super"}}
    )
    access_id = created.json()["id"]

    bodies = [
        created.text,
        (await client.get(f"{BASE}/accesses")).text,
        (await client.get(f"{BASE}/accesses/{access_id}")).text,
        (await client.get(f"{BASE}/connectors")).text,
    ]

    assert all("sk-super" not in body for body in bodies)
