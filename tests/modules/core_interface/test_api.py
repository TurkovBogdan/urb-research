"""core_interface: HTTP-поверхность — значения, схема, обновление, сброс."""

from __future__ import annotations

import pytest

from src.modules.core_interface import crud, registry

pytestmark = pytest.mark.db

BASE = "/internal/core/interface"


async def test_values_are_effective_even_with_an_empty_table(client):
    r = await client.get(f"{BASE}/settings")

    assert r.status_code == 200
    body = r.json()
    assert body["values"]["interface_theme"] == "dark"
    assert body["values"]["interface_font_reading_size"] == 14
    assert body["schema"] is None


async def test_start_request_carries_the_schema(client):
    r = await client.get(f"{BASE}/settings", params={"include_schema": "true"})

    by_key = {field["key"]: field for field in r.json()["schema"]}
    assert by_key["interface_theme"]["options"] == ["dark", "light", "system"]
    assert by_key["interface_nav_document"]["type"] == "boolean"


async def test_schema_has_its_own_route(client):
    r = await client.get(f"{BASE}/settings/schema")

    assert r.status_code == 200
    assert [field["key"] for field in r.json()["schema"]] == list(registry.SETTINGS)


async def test_patch_touches_only_the_keys_it_carries(client):
    await crud.upsert_many({"interface_font": "golos"})

    r = await client.patch(f"{BASE}/settings", json={"values": {"interface_theme": "light"}})

    assert r.status_code == 200
    assert r.json()["values"]["interface_theme"] == "light"
    assert r.json()["values"]["interface_font"] == "golos"
    assert await crud.list_all() == {"interface_theme": "light", "interface_font": "golos"}


async def test_rejected_batch_names_every_guilty_key_and_writes_nothing(client):
    r = await client.patch(
        f"{BASE}/settings",
        json={
            "values": {
                "interface_theme": "plaid",
                "interface_font_reading_size": 19,
                "interface_nope": "x",
                "interface_font": "golos",
            }
        },
    )

    assert r.status_code == 422
    assert set(r.json()["fields"]) == {
        "interface_theme",
        "interface_font_reading_size",
        "interface_nope",
    }
    assert await crud.list_all() == {}


async def test_reset_brings_back_the_default(client):
    await crud.upsert_many({"interface_theme": "light", "interface_font": "golos"})

    r = await client.post(f"{BASE}/settings/reset", json={"keys": ["interface_theme"]})

    assert r.json()["values"]["interface_theme"] == "dark"
    assert await crud.list_all() == {"interface_font": "golos"}


async def test_reset_of_an_unknown_key_is_rejected(client):
    r = await client.post(f"{BASE}/settings/reset", json={"keys": ["interface_nope"]})

    assert r.status_code == 422
    assert set(r.json()["fields"]) == {"interface_nope"}


async def test_empty_reset_list_erases_nothing(client):
    await crud.upsert_many({"interface_theme": "light"})

    r = await client.post(f"{BASE}/settings/reset", json={"keys": []})

    assert r.status_code == 200
    assert await crud.list_all() == {"interface_theme": "light"}


async def test_no_delete_route_exists(client):
    assert (await client.delete(f"{BASE}/settings")).status_code == 405
