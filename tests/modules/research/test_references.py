"""research: разрешение ссылок-кодов из тела (``TYPE@hash``) в заголовки сущностей."""

from __future__ import annotations

import pytest

from src.modules.research.crud import area as area_crud
from src.modules.research.crud import group as group_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import references as references_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.web_search.crud import page as page_crud

pytestmark = pytest.mark.db


async def test_resolves_a_group_code(db):
    group = await group_crud.group_create(title="Экология")

    labels = await references_crud.resolve_labels([f"GROUP@{group.code}"])

    assert labels == {f"GROUP@{group.code}": "Экология"}


async def test_resolves_every_type_in_one_call(db):
    group = await group_crud.group_create(title="Полка")
    research = await research_crud.research_create(title="Иссл", group_code=group.code)
    area = await area_crud.area_create(research_code=research.code, title="Область")
    note = await note_crud.note_create(
        research_code=research.code, kind="idea", title="Заметка"
    )
    query = await source_query_crud.source_query_create(
        research_code=research.code,
        area_code=area.code,
        search_code="0" * 22,
        query="urban parks",
    )
    page = await page_crud.page_upsert(url="https://ex.com/1", title="Страница")
    source = await source_document_crud.source_document_create(
        research_code=research.code,
        area_code=area.code,
        query_code=query.code,
        page_code=page.code,
    )

    labels = await references_crud.resolve_labels(
        [
            f"GROUP@{group.code}",
            f"RESEARCH@{research.code}",
            f"AREA@{area.code}",
            f"NOTE@{note.code}",
            f"QUERY@{query.code}",
            f"SOURCE@{source.code}",
        ]
    )

    assert labels == {
        f"GROUP@{group.code}": "Полка",
        f"RESEARCH@{research.code}": "Иссл",
        f"AREA@{area.code}": "Область",
        f"NOTE@{note.code}": "Заметка",
        # У поиска своего заголовка нет — пилюля показывает текст запроса.
        f"QUERY@{query.code}": "urban parks",
        # У источника — тоже нет: заголовок приезжает из страницы web_search.
        f"SOURCE@{source.code}": "Страница",
    }


async def test_unknown_and_untagged_codes_are_skipped(db):
    group = await group_crud.group_create(title="Полка")

    labels = await references_crud.resolve_labels(
        [f"GROUP@{group.code}", "GROUP@" + "0" * 22, group.code, "WAT@x"]
    )

    assert labels == {f"GROUP@{group.code}": "Полка"}


async def test_empty_input_hits_no_query(db):
    assert await references_crud.resolve_labels([]) == {}
