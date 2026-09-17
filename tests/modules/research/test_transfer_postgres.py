"""Круг «экспорт → импорт» на настоящем PostgreSQL по схеме из миграций.

Остальные тесты переноса идут на sqlite в памяти, и в этом их слепое пятно: вставка пачкой с
``ON CONFLICT DO NOTHING`` берётся из **диалектного** модуля (`sqlite_insert` против
`pg_insert`), а схему им строит `create_all`, а не цепочка миграций. Обе подмены умеют молчать:
на sqlite всё зелено, а на боевой базе приезжает другой SQL и другие ограничения.

Ярус `heavy` — без `TEST_PG_DSN` тест сам скипается (см. `AGENTS/docs/workflow/testing.md`).
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, func, select

from src.apps.app.modules import build_modules
from src.core.config import Config
from src.core.database import close_database, init_database, session_scope, write_scope
from src.core.database.migrations import AlembicRunner
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.research.transfer.constants import (
    ENTITY_AREAS,
    ENTITY_NOTES,
    ENTITY_PAGES,
    ENTITY_RESEARCH,
    ENTITY_SOURCES,
    IMPORT_MODE_NEWER,
)
from src.modules.research.transfer.export import export_research
from src.modules.research.transfer.runner import import_archive
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as result_crud
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.models.query_result import WebSearchQueryResult

pytestmark = pytest.mark.heavy

_PAGES = ("https://example.org/alpha", "https://example.org/beta")


async def _seed() -> str:
    """Исследование с областью, заметкой, прогоном поиска и двумя источниками с материалом."""
    research = await research_crud.research_create(title="Перенос на PostgreSQL")
    area = await area_crud.area_create(research_code=research.code, title="Область")
    await note_crud.note_create(
        research_code=research.code,
        kind="result",
        title="Вывод",
        body=f"ссылка на AREA@{area.code}",
    )
    search = await query_crud.query_create(
        search_engine="stub", fetch_engine="stub", query="запрос"
    )
    source_query = await source_query_crud.source_query_create(
        research_code=research.code,
        area_code=area.code,
        search_code=search.code,
        query="запрос",
    )
    for rank, url in enumerate(_PAGES):
        page = await page_crud.page_upsert(url, title=f"Страница {rank}")
        await page_crud.page_set_body(page.code, body=f"# материал {rank}")
        await result_crud.result_add(
            query_code=search.code, page_code=page.code, rank=rank, summary=f"снип {rank}"
        )
        await source_document_crud.source_document_create(
            research_code=research.code,
            area_code=area.code,
            query_code=source_query.code,
            page_code=page.code,
            summary=f"снип {rank}",
        )
    await research_crud.research_update(research.code, body=f"свод по AREA@{area.code}")
    return research.code


async def _wipe() -> None:
    async with write_scope() as s:
        for model in (
            ResearchSourceDocument,
            ResearchSourceQuery,
            ResearchNote,
            ResearchArea,
            Research,
            WebSearchQueryResult,
            WebSearchQuery,
            WebSearchPage,
        ):
            await s.execute(delete(model))


async def _count(model) -> int:
    async with session_scope() as s:
        return (await s.execute(select(func.count()).select_from(model))).scalar_one()


async def test_the_round_trip_runs_on_the_production_database(config: Config, tmp_path):
    engine = await init_database(config)
    try:
        # Позитивный контроль: без него тест, случайно оставшийся на sqlite, был бы зелёным и
        # ровно ничего не проверял — а смысл его существования именно в диалекте.
        assert engine.dialect.name == "postgresql"
        await AlembicRunner(modules=build_modules()).upgrade_head(engine)

        research_code = await _seed()
        archive = await export_research(research_code, tmp_path / "postgres.urch")
        assert archive.manifest.counts[ENTITY_SOURCES] == 2
        assert archive.manifest.source.alembic_heads, "манифест обязан назвать головы боевой базы"

        await _wipe()
        _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

        assert report.counts[ENTITY_RESEARCH]["created"] == 1
        assert report.counts[ENTITY_AREAS]["created"] == 1
        assert report.counts[ENTITY_NOTES]["created"] == 1
        assert report.counts[ENTITY_SOURCES]["created"] == 2
        assert report.counts[ENTITY_PAGES]["created"] == 2
        assert await _count(WebSearchQueryResult) == 2

        async with session_scope() as s:
            pages = (await s.execute(select(WebSearchPage))).scalars().all()
        assert {page.body for page in pages} == {"# материал 0", "# материал 1"}

        # Второй заход идёт по диалектной ветке ``ON CONFLICT DO NOTHING`` — на sqlite она другая.
        _, repeat = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

        assert repeat.counts[ENTITY_SOURCES]["created"] == 0
        assert repeat.counts[ENTITY_PAGES]["created"] == 0
        assert await _count(Research) == 1
        assert await _count(ResearchSourceDocument) == 2
        assert await _count(WebSearchQueryResult) == 2
    finally:
        await close_database()
