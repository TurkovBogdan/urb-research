"""HTTP-API модуля research (/internal/research): группа в списке и в детали, удаление,
переименование."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.database import close_database, init_database, session_scope
from src.core.database.runtime import Base
from src.modules.research.api import router
from src.modules.research.constants import DOC_FILTERED, DOC_KEPT
from src.modules.research.models.research import Research
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import group as group_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.web_search.crud import page as page_crud

pytestmark = pytest.mark.db


@pytest.fixture
async def app(config: Config):
    engine = await init_database(config)
    import src.modules.research.models  # noqa: F401 — register research tables
    import src.modules.web_search.models  # noqa: F401 — source join target

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    fastapi_app = FastAPI()
    register_exception_handlers(fastapi_app)
    fastapi_app.include_router(router, prefix="/internal/research")
    try:
        yield fastapi_app
    finally:
        await close_database()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def test_list_reports_the_group(client):
    group = await group_crud.group_create(title="Экология", icon="flask")
    await research_crud.research_create(title="Парки", group_code=group.code)

    body = (await client.get("/internal/research/researches")).json()

    row = body["items"][0]
    assert row["group_code"] == f"GROUP@{group.code}"
    assert row["group_name"] == "Экология"


async def test_list_keeps_ungrouped_researches(client):
    """Тот же внешний join, что и в MCP: неразложенное исследование не должно выпасть."""
    group = await group_crud.group_create(title="Полка")
    await research_crud.research_create(title="На полке", group_code=group.code)
    await research_crud.research_create(title="Без полки")

    body = (await client.get("/internal/research/researches")).json()

    assert body["total"] == 2
    by_title = {row["title"]: row for row in body["items"]}
    assert by_title["Без полки"]["group_code"] is None
    assert by_title["Без полки"]["group_name"] == ""


async def test_list_keeps_its_counters(client):
    """Полка добавлена рядом со счётчиками, а не вместо них."""
    await research_crud.research_create(title="R")

    row = (await client.get("/internal/research/researches")).json()["items"][0]

    assert row["area_count"] == 0 and row["query_count"] == 0
    assert row["document_kept"] == 0 and row["document_filtered"] == 0


async def test_detail_reports_the_group(client):
    group = await group_crud.group_create(title="Экология")
    research = await research_crud.research_create(
        title="Парки", body="# Итог", group_code=group.code
    )

    body = (await client.get(f"/internal/research/researches/{research.code}")).json()

    assert body["group_code"] == f"GROUP@{group.code}"
    assert body["group_name"] == "Экология"
    assert body["body"] == "# Итог"


async def test_detail_without_group(client):
    research = await research_crud.research_create(title="Сам по себе")

    body = (await client.get(f"/internal/research/researches/{research.code}")).json()

    assert body["group_code"] is None and body["group_name"] == ""


async def test_detail_missing_is_404(client):
    r = await client.get("/internal/research/researches/" + "0" * 22)

    assert r.status_code == 404


# ── Группы: полный CRUD (единственная write-поверхность модуля) ────────────────


async def test_create_group_returns_201_and_the_row(client):
    r = await client.post(
        "/internal/research/groups",
        json={
            "title": "Экология",
            "description": "d",
            "icon": "flask",
            "color": "green",
            "sort": 900,
        },
    )

    assert r.status_code == 201
    body = r.json()
    assert body["code"].startswith("GROUP@")
    assert (body["title"], body["icon"], body["color"], body["sort"]) == (
        "Экология",
        "flask",
        "green",
        900,
    )


async def test_create_group_defaults_sort(client):
    body = (await client.post("/internal/research/groups", json={"title": "G"})).json()

    assert body["sort"] == 500 and body["description"] == ""
    assert body["icon"] == "" and body["color"] == ""


async def test_update_group_replaces_the_look(client):
    """Тело правки полное: цвет и иконка приходят вместе, как их и выбирают в окне."""
    group = await group_crud.group_create(title="Экология", icon="flask", color="green")

    body = (
        await client.put(
            f"/internal/research/groups/GROUP@{group.code}",
            json={"title": "Экология", "icon": "leaf", "color": "teal"},
        )
    ).json()

    assert (body["icon"], body["color"]) == ("leaf", "teal")


async def test_update_group_clears_the_colour(client):
    """Пустая строка снимает цвет: окно шлёт её, когда человек выбрал плитку «без цвета»."""
    group = await group_crud.group_create(title="Экология", color="green")

    body = (
        await client.put(
            f"/internal/research/groups/GROUP@{group.code}",
            json={"title": "Экология", "color": ""},
        )
    ).json()

    assert body["color"] == ""


async def test_group_list_carries_the_look(client):
    await group_crud.group_create(title="Экология", icon="flask", color="green")

    rows = (await client.get("/internal/research/groups")).json()

    assert (rows[0]["icon"], rows[0]["color"]) == ("flask", "green")


async def test_create_group_rejects_empty_title(client):
    r = await client.post("/internal/research/groups", json={"title": ""})

    assert r.status_code == 422


async def test_list_groups_is_in_display_order(client):
    await group_crud.group_create(title="Бета", sort=100)
    await group_crud.group_create(title="Альфа", sort=900)

    rows = (await client.get("/internal/research/groups")).json()

    assert [row["title"] for row in rows] == ["Альфа", "Бета"]


async def test_get_group(client):
    group = await group_crud.group_create(title="Полка")

    body = (await client.get(f"/internal/research/groups/{group.code}")).json()

    assert body["code"] == f"GROUP@{group.code}"


async def test_update_group_replaces_the_card(client):
    group = await group_crud.group_create(title="Старое", description="d", icon="folder")

    body = (
        await client.put(
            f"/internal/research/groups/{group.code}",
            json={"title": "Новое", "icon": "flask"},
        )
    ).json()

    assert body["title"] == "Новое" and body["icon"] == "flask"
    assert body["description"] == ""


async def test_update_group_keeps_sort_when_omitted(client):
    group = await group_crud.group_create(title="G", sort=900)

    body = (
        await client.put(f"/internal/research/groups/{group.code}", json={"title": "G"})
    ).json()

    assert body["sort"] == 900


async def test_update_group_sort_zero_is_not_swallowed(client):
    """Ноль — валидная позиция (полка в самый низ), а не «поле не прислали»."""
    group = await group_crud.group_create(title="G", sort=900)

    body = (
        await client.put(
            f"/internal/research/groups/{group.code}", json={"title": "G", "sort": 0}
        )
    ).json()

    assert body["sort"] == 0


async def test_delete_group_is_204_and_keeps_researches(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)

    r = await client.delete(f"/internal/research/groups/{group.code}")

    assert r.status_code == 204
    detail = (await client.get(f"/internal/research/researches/{research.code}")).json()
    assert detail["group_code"] is None and detail["title"] == "R"


async def test_missing_group_is_404_on_every_verb(client):
    missing = "0" * 22

    assert (await client.get(f"/internal/research/groups/{missing}")).status_code == 404
    put = await client.put(f"/internal/research/groups/{missing}", json={"title": "X"})
    assert put.status_code == 404
    assert (await client.delete(f"/internal/research/groups/{missing}")).status_code == 404


# ── Привязка исследования к полке ─────────────────────────────────────────────


async def test_set_research_group_files_and_unfiles(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R")
    url = f"/internal/research/researches/{research.code}/group"

    filed = (await client.put(url, json={"group_code": f"GROUP@{group.code}"})).json()
    assert filed["group_code"] == f"GROUP@{group.code}"
    assert filed["group_name"] == "Полка"

    unfiled = (await client.put(url, json={"group_code": None})).json()
    assert unfiled["group_code"] is None and unfiled["group_name"] == ""


async def test_set_research_group_validates_both_codes(client):
    research = await research_crud.research_create(title="R")
    missing = "0" * 22

    bad_group = await client.put(
        f"/internal/research/researches/{research.code}/group",
        json={"group_code": missing},
    )
    assert bad_group.status_code == 404

    bad_research = await client.put(
        f"/internal/research/researches/{missing}/group", json={"group_code": None}
    )
    assert bad_research.status_code == 404


# ── Фильтр списка по полке ────────────────────────────────────────────────────


async def test_list_filters_by_group(client):
    group = await group_crud.group_create(title="Полка")
    await research_crud.research_create(title="На полке", group_code=group.code)
    await research_crud.research_create(title="Без полки")

    body = (
        await client.get("/internal/research/researches", params={"group_code": group.code})
    ).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "На полке"


async def test_list_filters_the_ungrouped_with_an_empty_code(client):
    group = await group_crud.group_create(title="Полка")
    await research_crud.research_create(title="На полке", group_code=group.code)
    await research_crud.research_create(title="Без полки")

    body = (
        await client.get("/internal/research/researches", params={"group_code": ""})
    ).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Без полки"


async def test_list_with_unknown_group_is_404(client):
    r = await client.get(
        "/internal/research/researches", params={"group_code": "0" * 22}
    )

    assert r.status_code == 404


async def test_group_list_carries_research_counts(client):
    group = await group_crud.group_create(title="Полка")
    empty = await group_crud.group_create(title="Пустая")
    await research_crud.research_create(title="R1", group_code=group.code)
    await research_crud.research_create(title="R2", group_code=group.code)
    await research_crud.research_create(title="Без полки")

    rows = {row["title"]: row for row in (await client.get("/internal/research/groups")).json()}

    assert rows["Полка"]["research_count"] == 2
    assert rows["Пустая"]["research_count"] == 0


async def test_group_count_drops_when_a_research_is_unfiled(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)

    await client.put(
        f"/internal/research/researches/{research.code}/group", json={"group_code": None}
    )

    rows = (await client.get("/internal/research/groups")).json()
    assert rows[0]["research_count"] == 0


async def test_list_accepts_an_empty_hash_as_the_ungrouped_filter(client):
    """`GROUP@` без хеша — псевдо-полка «Без группы»: strip_prefix даёт пустой код."""
    group = await group_crud.group_create(title="Полка")
    await research_crud.research_create(title="На полке", group_code=group.code)
    await research_crud.research_create(title="Без полки")

    body = (
        await client.get("/internal/research/researches", params={"group_code": "GROUP@"})
    ).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Без полки"


# ── Сортировка списка ─────────────────────────────────────────────────────────

RESEARCHES = "/internal/research/researches"


async def _titles(client, **params) -> list[str]:
    body = (await client.get(RESEARCHES, params=params)).json()
    return [row["title"] for row in body["items"]]


async def _set_dates(code: str, *, created_at: datetime, updated_at: datetime) -> None:
    """Даты пишем напрямую: колонки с precision=0, а подряд созданные строки делят одну секунду —
    сортировку по датам иначе решал бы тайбрейк по случайному коду."""
    async with session_scope() as s:
        row = await s.get(Research, code)
        row.created_at = created_at
        row.updated_at = updated_at


async def _with_areas(title: str, count: int) -> str:
    research = await research_crud.research_create(title=title)
    for index in range(count):
        await area_crud.area_create(research_code=research.code, title=f"Область {index}")
    return research.code


async def _with_documents(title: str, *, kept: int, filtered: int) -> str:
    research = await research_crud.research_create(title=title)
    area = await area_crud.area_create(research_code=research.code, title="Область")
    query = await source_query_crud.source_query_create(
        research_code=research.code,
        area_code=area.code,
        search_code="0" * 22,
        query="q",
    )
    for index in range(kept + filtered):
        page = await page_crud.page_upsert(f"https://example.test/{title}/{index}")
        document = await source_document_crud.source_document_create(
            research_code=research.code,
            area_code=area.code,
            query_code=query.code,
            page_code=page.code,
        )
        status = DOC_KEPT if index < kept else DOC_FILTERED
        await source_document_crud.source_document_review(
            document.code, status=status, relevance=5
        )
    return research.code


async def test_list_sorts_by_title(client):
    for title in ("Бета", "Альфа", "Гамма"):
        await research_crud.research_create(title=title)

    assert await _titles(client, sort_by="title", sort_dir="asc") == ["Альфа", "Бета", "Гамма"]
    assert await _titles(client, sort_by="title", sort_dir="desc") == ["Гамма", "Бета", "Альфа"]


async def test_list_sorts_by_dates_independently(client):
    """Создано и обновлено — разные ключи: строка, созданная раньше, может быть свежее."""
    old = await research_crud.research_create(title="Старое")
    new = await research_crud.research_create(title="Новое")
    await _set_dates(
        old.code, created_at=datetime(2026, 1, 1), updated_at=datetime(2026, 8, 1)
    )
    await _set_dates(
        new.code, created_at=datetime(2026, 6, 1), updated_at=datetime(2026, 2, 1)
    )

    assert await _titles(client, sort_by="created_at", sort_dir="desc") == ["Новое", "Старое"]
    assert await _titles(client, sort_by="updated_at", sort_dir="desc") == ["Старое", "Новое"]


async def test_list_sorts_by_area_count(client):
    await _with_areas("Одна", 1)
    await _with_areas("Три", 3)
    await _with_areas("Пусто", 0)

    assert await _titles(client, sort_by="area_count", sort_dir="desc") == [
        "Три",
        "Одна",
        "Пусто",
    ]


async def test_list_sorts_by_kept_and_filtered_separately(client):
    """Счётчики источников — разные подзапросы: у сортировки по принятым свой порядок."""
    await _with_documents("Отсеивает", kept=1, filtered=3)
    await _with_documents("Принимает", kept=2, filtered=0)

    by_kept = await _titles(client, sort_by="document_kept", sort_dir="desc")
    by_filtered = await _titles(client, sort_by="document_filtered", sort_dir="desc")

    assert by_kept == ["Принимает", "Отсеивает"]
    assert by_filtered == ["Отсеивает", "Принимает"]


async def test_sorting_by_a_count_respects_the_group_filter(client):
    """Подзапрос-счётчик в ORDER BY не должен ломать ни фильтр по полке, ни его total."""
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="На полке", group_code=group.code)
    await area_crud.area_create(research_code=research.code, title="Область")
    await _with_areas("Без полки", 5)

    body = (
        await client.get(
            RESEARCHES, params={"group_code": group.code, "sort_by": "area_count"}
        )
    ).json()

    assert body["total"] == 1
    assert [row["title"] for row in body["items"]] == ["На полке"]


async def test_unknown_sort_field_falls_back_to_created_at(client):
    """Белый список — защита от инъекции: неизвестный ключ не ошибка, а порядок по умолчанию."""
    for title in ("Первое", "Второе"):
        await research_crud.research_create(title=title)
    default_order = await _titles(client, sort_dir="desc")

    assert await _titles(client, sort_by="title; DROP TABLE", sort_dir="desc") == default_order


# ── Удаление: исследование / область / поиск / заметка ────────────────────────

BASE = "/internal/research"
MISSING = "0" * 22


async def _build_tree(title: str, *, url: str, group_code: str | None = None) -> dict[str, str]:
    """Дерево одного исследования: область → поиск → источник (на реальной странице) + заметка."""
    research = await research_crud.research_create(title=title, group_code=group_code)
    area = await area_crud.area_create(research_code=research.code, title="Область")
    query = await source_query_crud.source_query_create(
        research_code=research.code,
        area_code=area.code,
        search_code="0" * 22,
        query="как оно работает",
    )
    page = await page_crud.page_upsert(url, title="Страница")
    document = await source_document_crud.source_document_create(
        research_code=research.code,
        area_code=area.code,
        query_code=query.code,
        page_code=page.code,
    )
    note = await note_crud.note_create(
        research_code=research.code, kind="result", title="Заметка"
    )
    return {
        "research": research.code,
        "area": area.code,
        "query": query.code,
        "document": document.code,
        "note": note.code,
        "page": page.code,
    }


@pytest.fixture
async def tree():
    return await _build_tree("Исследование", url="https://example.test/a")


@pytest.fixture
async def neighbour():
    """Второе, независимое дерево — контроль, что удаление не выходит за своё поддерево."""
    return await _build_tree("Соседнее", url="https://example.test/b")


async def test_delete_research_takes_everything_under_it(client, tree):
    r = await client.delete(f"{BASE}/researches/{tree['research']}")

    assert r.status_code == 204
    assert (await client.get(f"{BASE}/researches/{tree['research']}")).status_code == 404
    assert (await client.get(f"{BASE}/areas/{tree['area']}")).status_code == 404
    assert (await client.get(f"{BASE}/source-queries/{tree['query']}")).status_code == 404
    assert (await client.get(f"{BASE}/source-documents/{tree['document']}")).status_code == 404
    assert (await client.get(f"{BASE}/notes/{tree['note']}")).status_code == 404


async def test_delete_area_keeps_the_research_and_its_notes(client, tree):
    r = await client.delete(f"{BASE}/areas/{tree['area']}")

    assert r.status_code == 204
    assert (await client.get(f"{BASE}/researches/{tree['research']}")).status_code == 200
    assert (await client.get(f"{BASE}/notes/{tree['note']}")).status_code == 200
    assert (await client.get(f"{BASE}/source-queries/{tree['query']}")).status_code == 404
    assert (await client.get(f"{BASE}/source-documents/{tree['document']}")).status_code == 404


async def test_delete_source_query_takes_its_sources_only(client, tree):
    r = await client.delete(f"{BASE}/source-queries/{tree['query']}")

    assert r.status_code == 204
    assert (await client.get(f"{BASE}/source-documents/{tree['document']}")).status_code == 404
    assert (await client.get(f"{BASE}/areas/{tree['area']}")).status_code == 200


async def test_delete_note_keeps_the_research(client, tree):
    r = await client.delete(f"{BASE}/notes/{tree['note']}")

    assert r.status_code == 204
    detail = (await client.get(f"{BASE}/researches/{tree['research']}")).json()
    assert detail["notes"] == []


async def test_deleted_children_leave_the_detail_counters_empty(client, tree):
    await client.delete(f"{BASE}/areas/{tree['area']}")

    detail = (await client.get(f"{BASE}/researches/{tree['research']}")).json()
    assert detail["areas"] == [] and detail["queries"] == []
    documents = (await client.get(f"{BASE}/researches/{tree['research']}/documents")).json()
    assert documents == []


async def test_delete_of_a_missing_entity_is_404(client):
    for path in ("researches", "areas", "source-queries", "notes"):
        assert (await client.delete(f"{BASE}/{path}/{MISSING}")).status_code == 404


async def test_delete_accepts_a_prefixed_code(client, tree):
    """Коды приходят с фронта в проводной форме (``RESEARCH@…``) — префикс снимается на входе."""
    r = await client.delete(f"{BASE}/researches/RESEARCH@{tree['research']}")

    assert r.status_code == 204


async def test_delete_is_scoped_to_its_own_subtree(client, tree, neighbour):
    """Каскад ручной (FK-каскада в sqlite нет) — WHERE каждого шага должен держаться своего кода."""
    await client.delete(f"{BASE}/researches/{tree['research']}")

    assert (await client.get(f"{BASE}/researches/{neighbour['research']}")).status_code == 200
    assert (await client.get(f"{BASE}/areas/{neighbour['area']}")).status_code == 200
    assert (await client.get(f"{BASE}/source-queries/{neighbour['query']}")).status_code == 200
    assert (
        await client.get(f"{BASE}/source-documents/{neighbour['document']}")
    ).status_code == 200
    assert (await client.get(f"{BASE}/notes/{neighbour['note']}")).status_code == 200


async def test_delete_drops_the_research_from_the_list(client, tree, neighbour):
    await client.delete(f"{BASE}/researches/{tree['research']}")

    body = (await client.get(f"{BASE}/researches")).json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Соседнее"


async def test_delete_keeps_the_shelf_and_drops_its_counter(client):
    """Полка переживает исследование: удаление содержимого — не удаление раскладки."""
    group = await group_crud.group_create(title="Полка")
    tree = await _build_tree("На полке", url="https://example.test/c", group_code=group.code)

    await client.delete(f"{BASE}/researches/{tree['research']}")

    rows = (await client.get(f"{BASE}/groups")).json()
    assert [(row["title"], row["research_count"]) for row in rows] == [("Полка", 0)]


async def test_delete_keeps_the_web_search_page(client, tree):
    """Источник ссылается на страницу, а не владеет ею — она общая для всех исследований."""
    await client.delete(f"{BASE}/researches/{tree['research']}")

    assert await page_crud.page_get_by_code(tree["page"]) is not None


async def test_second_delete_of_the_same_code_is_404(client, tree):
    assert (await client.delete(f"{BASE}/researches/{tree['research']}")).status_code == 204
    assert (await client.delete(f"{BASE}/researches/{tree['research']}")).status_code == 404


async def test_delete_area_keeps_the_sibling_area(client, tree):
    sibling = await area_crud.area_create(research_code=tree["research"], title="Вторая")

    await client.delete(f"{BASE}/areas/{tree['area']}")

    detail = (await client.get(f"{BASE}/researches/{tree['research']}")).json()
    assert [area["code"] for area in detail["areas"]] == [f"AREA@{sibling.code}"]


async def test_delete_source_query_keeps_the_sibling_run_and_its_sources(client, tree):
    sibling = await source_query_crud.source_query_create(
        research_code=tree["research"],
        area_code=tree["area"],
        search_code="2" * 22,
        query="второй прогон",
    )
    kept_source = await source_document_crud.source_document_create(
        research_code=tree["research"],
        area_code=tree["area"],
        query_code=sibling.code,
        page_code=tree["page"],
    )

    await client.delete(f"{BASE}/source-queries/{tree['query']}")

    assert (await client.get(f"{BASE}/source-queries/{sibling.code}")).status_code == 200
    assert (await client.get(f"{BASE}/source-documents/{kept_source.code}")).status_code == 200


async def test_delete_note_keeps_the_sibling_note(client, tree):
    sibling = await note_crud.note_create(
        research_code=tree["research"], kind="idea", title="Вторая"
    )

    await client.delete(f"{BASE}/notes/{tree['note']}")

    detail = (await client.get(f"{BASE}/researches/{tree['research']}")).json()
    assert [note["code"] for note in detail["notes"]] == [f"NOTE@{sibling.code}"]


# ── Удаление полки: судьба исследований ───────────────────────────────────────


async def test_delete_group_detaches_by_default(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)

    assert (await client.delete(f"/internal/research/groups/{group.code}")).status_code == 204

    kept = await research_crud.research_get(research.code)
    assert kept is not None and kept.group_code is None


async def test_delete_group_moves_researches(client):
    source = await group_crud.group_create(title="Откуда")
    target = await group_crud.group_create(title="Куда")
    research = await research_crud.research_create(title="R", group_code=source.code)

    r = await client.delete(
        f"/internal/research/groups/{source.code}",
        params={"researches": "move", "move_to": f"GROUP@{target.code}"},
    )

    assert r.status_code == 204
    assert (await research_crud.research_get(research.code)).group_code == target.code


async def test_delete_group_deletes_researches_with_their_content(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)
    area = await area_crud.area_create(research_code=research.code, title="A")

    r = await client.delete(
        f"/internal/research/groups/{group.code}", params={"researches": "delete"}
    )

    assert r.status_code == 204
    assert await research_crud.research_get(research.code) is None
    assert await area_crud.area_get(area.code) is None


async def test_delete_group_leaves_other_groups_researches_alone(client):
    doomed = await group_crud.group_create(title="Удаляемая")
    other = await group_crud.group_create(title="Другая")
    kept = await research_crud.research_create(title="Чужое", group_code=other.code)
    await research_crud.research_create(title="Своё", group_code=doomed.code)

    await client.delete(
        f"/internal/research/groups/{doomed.code}", params={"researches": "delete"}
    )

    assert (await research_crud.research_get(kept.code)).group_code == other.code


async def test_delete_group_move_without_target_is_400(client):
    group = await group_crud.group_create(title="Полка")

    r = await client.delete(
        f"/internal/research/groups/{group.code}", params={"researches": "move"}
    )

    assert r.status_code == 400
    assert await group_crud.group_get(group.code) is not None


async def test_delete_group_move_into_itself_is_400(client):
    group = await group_crud.group_create(title="Полка")

    r = await client.delete(
        f"/internal/research/groups/{group.code}",
        params={"researches": "move", "move_to": group.code},
    )

    assert r.status_code == 400


async def test_delete_group_move_to_missing_group_is_404(client):
    group = await group_crud.group_create(title="Полка")

    r = await client.delete(
        f"/internal/research/groups/{group.code}",
        params={"researches": "move", "move_to": "0" * 22},
    )

    assert r.status_code == 404
    assert await group_crud.group_get(group.code) is not None


async def test_delete_group_rejects_an_unknown_strategy(client):
    group = await group_crud.group_create(title="Полка")

    r = await client.delete(
        f"/internal/research/groups/{group.code}", params={"researches": "burn"}
    )

    assert r.status_code == 422


async def test_rename_research_returns_the_fresh_detail(client):
    research = await research_crud.research_create(title="Старое имя")

    r = await client.put(
        f"/internal/research/researches/{research.code}/title", json={"title": "Новое имя"}
    )

    assert r.status_code == 200
    assert r.json()["title"] == "Новое имя"
    assert (await research_crud.research_get(research.code)).title == "Новое имя"


async def test_rename_research_keeps_the_rest_of_the_artifact(client):
    """Ручка узкая: описание, тело и полка переименованием не затрагиваются."""
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(
        title="Было", description="Описание", body="Тело", group_code=group.code
    )

    body = (
        await client.put(
            f"/internal/research/researches/{research.code}/title", json={"title": "Стало"}
        )
    ).json()

    assert body["description"] == "Описание"
    assert body["body"] == "Тело"
    assert body["group_code"] == f"GROUP@{group.code}"


async def test_rename_research_accepts_a_prefixed_code(client):
    research = await research_crud.research_create(title="Было")

    r = await client.put(
        f"/internal/research/researches/RESEARCH@{research.code}/title", json={"title": "Стало"}
    )

    assert r.status_code == 200


async def test_rename_research_trims_the_title(client):
    research = await research_crud.research_create(title="Было")

    body = (
        await client.put(
            f"/internal/research/researches/{research.code}/title", json={"title": "  Стало  "}
        )
    ).json()

    assert body["title"] == "Стало"


@pytest.mark.parametrize("title", ["", "   ", "я" * 129])
async def test_rename_research_rejects_an_unusable_title(client, title):
    """Пусто, одни пробелы (срезаются ДО проверки длины) и длиннее колонки — все 422."""
    research = await research_crud.research_create(title="Было")

    r = await client.put(
        f"/internal/research/researches/{research.code}/title", json={"title": title}
    )

    assert r.status_code == 422
    assert (await research_crud.research_get(research.code)).title == "Было"


async def test_rename_missing_research_is_404(client):
    r = await client.put(
        f"/internal/research/researches/{'0' * 22}/title", json={"title": "Имя"}
    )

    assert r.status_code == 404


async def test_rename_area(client):
    research = await research_crud.research_create(title="Исследование")
    area = await area_crud.area_create(research_code=research.code, title="Было")

    r = await client.put(f"/internal/research/areas/{area.code}/title", json={"title": "Стало"})

    assert r.status_code == 200
    assert r.json()["title"] == "Стало"
    assert (await area_crud.area_get(area.code)).title == "Стало"


async def test_rename_missing_area_is_404(client):
    r = await client.put(
        f"/internal/research/areas/{'0' * 22}/title", json={"title": "Имя"}
    )

    assert r.status_code == 404


async def test_rename_note(client):
    research = await research_crud.research_create(title="Исследование")
    note = await note_crud.note_create(
        research_code=research.code, kind="result", title="Было"
    )

    r = await client.put(f"/internal/research/notes/{note.code}/title", json={"title": "Стало"})

    assert r.status_code == 200
    assert r.json()["title"] == "Стало"
    assert (await note_crud.note_get(note.code)).title == "Стало"


async def test_rename_note_keeps_its_kind(client):
    research = await research_crud.research_create(title="Исследование")
    note = await note_crud.note_create(
        research_code=research.code, kind="decision", title="Было"
    )

    body = (
        await client.put(
            f"/internal/research/notes/{note.code}/title", json={"title": "Стало"}
        )
    ).json()

    assert body["kind"] == "decision"


async def test_rename_missing_note_is_404(client):
    r = await client.put(f"/internal/research/notes/{'0' * 22}/title", json={"title": "Имя"})

    assert r.status_code == 404


# ── Полка исследования: пути, которыми ходит меню списка ──────────────────────


async def test_move_research_between_groups(client):
    """«Переложить на другую полку»: старая полка теряет строку, новая получает."""
    old = await group_crud.group_create(title="Старая")
    new = await group_crud.group_create(title="Новая")
    research = await research_crud.research_create(title="R", group_code=old.code)

    moved = (
        await client.put(
            f"/internal/research/researches/{research.code}/group",
            json={"group_code": f"GROUP@{new.code}"},
        )
    ).json()

    assert moved["group_code"] == f"GROUP@{new.code}"
    assert moved["group_name"] == "Новая"


async def test_move_research_shifts_the_group_counters(client):
    old = await group_crud.group_create(title="Старая")
    new = await group_crud.group_create(title="Новая")
    research = await research_crud.research_create(title="R", group_code=old.code)

    await client.put(
        f"/internal/research/researches/{research.code}/group",
        json={"group_code": new.code},
    )

    counts = {
        row["code"]: row["research_count"]
        for row in (await client.get("/internal/research/groups")).json()
    }
    assert counts[f"GROUP@{old.code}"] == 0
    assert counts[f"GROUP@{new.code}"] == 1


async def test_detach_research_from_its_group(client):
    """«Снять с полки»: исследование остаётся, полка остаётся, связи нет."""
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)

    detached = (
        await client.put(
            f"/internal/research/researches/{research.code}/group",
            json={"group_code": None},
        )
    ).json()

    assert detached["group_code"] is None
    assert await group_crud.group_get(group.code) is not None
    assert (await research_crud.research_get(research.code)) is not None


async def test_detaching_an_ungrouped_research_is_a_no_op(client):
    """Меню такого пункта не покажет, но повтор запроса не должен быть ошибкой."""
    research = await research_crud.research_create(title="R")

    r = await client.put(
        f"/internal/research/researches/{research.code}/group", json={"group_code": None}
    )

    assert r.status_code == 200
    assert r.json()["group_code"] is None


async def test_detached_research_moves_to_the_ungrouped_filter(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)

    await client.put(
        f"/internal/research/researches/{research.code}/group", json={"group_code": None}
    )

    ungrouped = (
        await client.get("/internal/research/researches", params={"group_code": ""})
    ).json()
    assert [row["code"] for row in ungrouped["items"]] == [f"RESEARCH@{research.code}"]


async def test_set_group_accepts_a_bare_group_code(client):
    """Меню шлёт код как получило (с префиксом), но голый тоже обязан резолвиться."""
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R")

    r = await client.put(
        f"/internal/research/researches/{research.code}/group",
        json={"group_code": group.code},
    )

    assert r.status_code == 200
    assert r.json()["group_code"] == f"GROUP@{group.code}"


async def test_moving_to_a_missing_group_keeps_the_current_one(client):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="R", group_code=group.code)

    r = await client.put(
        f"/internal/research/researches/{research.code}/group",
        json={"group_code": "0" * 22},
    )

    assert r.status_code == 404
    assert (await research_crud.research_get(research.code)).group_code == group.code


# ── Повтор получения материала ────────────────────────────────────────────────


async def _tree_with_broken_source(url: str) -> dict[str, str]:
    """Дерево, у которого материал источника не получен: страница в ``error``, источник тоже."""
    tree = await _build_tree("Сломанное", url=url)
    await page_crud.page_set_error(tree["page"], error="ConnectError")
    await source_document_crud.source_document_reset_by_codes([tree["document"]])
    return tree


async def test_refetch_research_documents_revives_a_broken_source(client, use_search):
    tree = await _tree_with_broken_source("https://example.test/broken")
    use_search(pages={"https://example.test/broken": "# материал"})

    r = await client.post(f"{BASE}/researches/{tree['research']}/documents/refetch")

    assert r.status_code == 200
    assert [row["status"] for row in r.json()] == ["pending"]
    detail = await client.get(f"{BASE}/source-documents/{tree['document']}")
    assert detail.json()["body"] == "# материал"


async def test_refetch_research_documents_reports_a_source_that_failed_again(client, use_search):
    tree = await _tree_with_broken_source("https://example.test/dead")
    use_search(pages={})

    r = await client.post(f"{BASE}/researches/{tree['research']}/documents/refetch")

    assert [row["status"] for row in r.json()] == ["error"]


async def test_refetch_research_documents_leaves_reviewed_sources_alone(client, use_search):
    """Кнопка чинит только то, что сломано: разобранный источник в её выборку не входит."""
    tree = await _build_tree("Разобранное", url="https://example.test/reviewed")
    await page_crud.page_set_body(tree["page"], body="# старое")
    await source_document_crud.source_document_review(
        tree["document"], status=DOC_KEPT, relevance=7
    )
    use_search(pages={"https://example.test/reviewed": "# новое"})

    r = await client.post(f"{BASE}/researches/{tree['research']}/documents/refetch")

    assert r.json() == []
    doc, _ = await source_document_crud.source_document_get(tree["document"])
    assert doc.status == DOC_KEPT


async def test_refetch_area_documents_takes_the_area_level(client, use_search):
    tree = await _tree_with_broken_source("https://example.test/area")
    use_search(pages={"https://example.test/area": "# материал"})

    r = await client.post(f"{BASE}/areas/{tree['area']}/documents/refetch")

    assert [row["code"] for row in r.json()] == [f"SOURCE@{tree['document']}"]


async def test_refetch_one_source_drops_its_verdict(client, use_search):
    """Пункт строки работает в любом статусе: материал перекачан — прежний вердикт снят."""
    tree = await _build_tree("Разобранное", url="https://example.test/again")
    await page_crud.page_set_body(tree["page"], body="# старое")
    await source_document_crud.source_document_review(
        tree["document"], status=DOC_FILTERED, relevance=3, note="слабо"
    )
    use_search(pages={"https://example.test/again": "# новое"})

    r = await client.post(f"{BASE}/source-documents/{tree['document']}/refetch")

    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    # Оценка и заметка переживают повтор: прежний разбор остаётся читаемым.
    assert r.json()["relevance"] == 3 and r.json()["note"] == "слабо"
    detail = await client.get(f"{BASE}/source-documents/{tree['document']}")
    assert detail.json()["body"] == "# новое"


async def test_refetch_one_source_missing(client):
    assert (await client.post(f"{BASE}/source-documents/{MISSING}/refetch")).status_code == 404


async def test_refetch_refuses_a_disabled_fetch_engine(client, use_search, monkeypatch):
    """Движок контента выключен — отказ до сети, а не молчаливый пустой прогон."""
    tree = await _tree_with_broken_source("https://example.test/off")
    engine = use_search(pages={})
    monkeypatch.setattr(engine, "available", lambda: False)

    r = await client.post(f"{BASE}/researches/{tree['research']}/documents/refetch")

    assert r.status_code == 400


# ── Глубокий поиск: по телам зон, заметок и материалу источников ──────────────


async def _tree_with_bodies() -> dict[str, str]:
    """Дерево, где искомое слово лежит ТОЛЬКО в телах — в названиях и описаниях его нет."""
    research = await research_crud.research_create(title="Исследование")
    area = await area_crud.area_create(research_code=research.code, title="Зона")
    await area_crud.area_update(area.code, body="Синтез про Оренбург и взносы")
    note = await note_crud.note_create(
        research_code=research.code, kind="result", title="Вывод"
    )
    await note_crud.note_update(note.code, body="Заметка упоминает ОРЕНБУРГ")
    query = await source_query_crud.source_query_create(
        research_code=research.code,
        area_code=area.code,
        search_code="0" * 22,
        query="q",
    )
    page = await page_crud.page_upsert("https://example.test/deep", title="Страница")
    await page_crud.page_set_body(page.code, body="Материал страницы: оренбург, тарифы")
    document = await source_document_crud.source_document_create(
        research_code=research.code,
        area_code=area.code,
        query_code=query.code,
        page_code=page.code,
    )
    quiet = await page_crud.page_upsert("https://example.test/quiet", title="Другая")
    await page_crud.page_set_body(quiet.code, body="Ничего интересного")
    other = await source_document_crud.source_document_create(
        research_code=research.code,
        area_code=area.code,
        query_code=query.code,
        page_code=quiet.code,
    )
    return {
        "research": research.code,
        "area": area.code,
        "note": note.code,
        "document": document.code,
        "other": other.code,
    }


async def test_deep_search_finds_bodies_across_kinds(client):
    tree = await _tree_with_bodies()

    body = (
        await client.get(f"{BASE}/researches/{tree['research']}/search", params={"q": "оренбург"})
    ).json()

    assert body["areas"] == [f"AREA@{tree['area']}"]
    assert body["notes"] == [f"NOTE@{tree['note']}"]
    assert body["sources"] == [f"SOURCE@{tree['document']}"]


async def test_deep_search_folds_case_for_cyrillic(client):
    """Главная причина искать в Python: у sqlite `LIKE` не складывает регистр кириллицы,
    а `lower('Ж')` возвращает 'Ж' — заглавный «ОРЕНБУРГ» в заметке иначе не нашёлся бы."""
    tree = await _tree_with_bodies()

    body = (
        await client.get(f"{BASE}/researches/{tree['research']}/search", params={"q": "ОрЕнБуРг"})
    ).json()

    assert body["notes"] == [f"NOTE@{tree['note']}"]
    assert body["areas"] and body["sources"]


async def test_deep_search_skips_what_does_not_match(client):
    tree = await _tree_with_bodies()

    body = (
        await client.get(f"{BASE}/researches/{tree['research']}/search", params={"q": "тарифы"})
    ).json()

    assert body["sources"] == [f"SOURCE@{tree['document']}"]
    assert body["areas"] == [] and body["notes"] == []


async def test_deep_search_ignores_a_too_short_query(client):
    """Строку набирают по букве: первая не должна ни грузить все тела, ни выглядеть отказом."""
    tree = await _tree_with_bodies()

    body = (
        await client.get(f"{BASE}/researches/{tree['research']}/search", params={"q": "о"})
    ).json()

    assert body == {"areas": [], "notes": [], "sources": []}


async def test_deep_search_stays_inside_its_research(client):
    tree = await _tree_with_bodies()
    stranger = await research_crud.research_create(title="Чужое")
    stranger_area = await area_crud.area_create(research_code=stranger.code, title="Зона")
    await area_crud.area_update(stranger_area.code, body="Тоже про Оренбург")

    body = (
        await client.get(f"{BASE}/researches/{tree['research']}/search", params={"q": "оренбург"})
    ).json()

    assert body["areas"] == [f"AREA@{tree['area']}"]


async def test_deep_search_missing_research_is_404(client):
    r = await client.get(f"{BASE}/researches/{MISSING}/search", params={"q": "оренбург"})

    assert r.status_code == 404


async def test_list_carries_the_group_look(client):
    """Строке нужен вид полки (иконка и цвет), чтобы плитка нарисовала её метку без второго запроса."""
    group = await group_crud.group_create(title="Экология", icon="flask", color="green")
    await research_crud.research_create(title="Парки", group_code=group.code)

    row = (await client.get("/internal/research/researches")).json()["items"][0]

    assert row["group_icon"] == "flask"
    assert row["group_color"] == "green"


async def test_list_group_look_is_empty_without_a_group(client):
    await research_crud.research_create(title="Сам по себе")

    row = (await client.get("/internal/research/researches")).json()["items"][0]

    assert row["group_icon"] == "" and row["group_color"] == ""
