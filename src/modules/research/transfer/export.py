"""Экспорт исследования в архив ``.urch`` — чистое чтение и потоковая запись.

Отбор идёт по цепочке сверху вниз: исследование → области и заметки → источниковые запросы →
прогоны поиска и их выдача → источники → страницы. Страницы берутся объединением двух множеств
(страницы источников и страницы выдачи): в живой базе выдача research-прогонов ложится на
источники один в один, но инвариантом это нигде не закреплено, и объединение дешевле, чем
однажды выгрузить источник без материала.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ulid import ULID

from src.core.module_state import module_store
from src.core.version import app_version
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    GROUP_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    PAGE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)
from src.modules.research.crud import transfer as transfer_crud
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.research.transfer.archive import ArchiveWriter
from src.modules.research.transfer.constants import (
    ENTITY_AREAS,
    ENTITY_GROUP,
    ENTITY_NOTES,
    ENTITY_PAGES,
    ENTITY_RESEARCH,
    ENTITY_SEARCHES,
    ENTITY_SEARCH_RESULTS,
    ENTITY_SOURCES,
    ENTITY_SOURCE_QUERIES,
    INSTALL_ID_KEY,
)
from src.modules.research.transfer.manifest import Manifest, ManifestRoot, ManifestSource
from src.modules.research.transfer.naming import archive_file_name
from src.modules.research.transfer.refs import collect_references
from src.modules.research.transfer.rows import row_to_json
from src.modules.web_search.services import transfer as web_search_transfer

RESEARCH_MODULE = "research"

_BODY_OMITTED = ("body",)
_SURROGATE_ID_OMITTED = ("id",)


@dataclass(frozen=True)
class ExportedArchive:
    """Готовый архив: путь на диске, имя для человека и манифест (для отчётов и тестов)."""

    path: Path
    file_name: str
    manifest: Manifest


async def install_id() -> str:
    """Идентификатор этой установки — чтобы импорт отличал свой архив от чужого.

    Живёт в общем хранилище состояния модулей: это внутренняя отметка, а не настройка
    оператора, и человеку её незачем ни видеть, ни менять.
    """
    store = module_store(RESEARCH_MODULE)
    existing = await store.get(INSTALL_ID_KEY)
    if existing:
        return str(existing)
    await store.seed_if_absent(INSTALL_ID_KEY, str(ULID()))
    return str(await store.get(INSTALL_ID_KEY))


async def export_research(research_code: str, path: Path) -> ExportedArchive:
    """Собрать архив исследования по указанному пути; вернуть его паспорт."""
    research = await transfer_crud.research_row(research_code)
    if research is None:
        raise LookupError(research_code)

    group = (
        await transfer_crud.group_row(research.group_code) if research.group_code else None
    )
    areas = await transfer_crud.rows_by_research(ResearchArea, research_code)
    notes = await transfer_crud.rows_by_research(ResearchNote, research_code)
    source_queries = await transfer_crud.rows_by_research(ResearchSourceQuery, research_code)
    sources = await transfer_crud.rows_by_research(ResearchSourceDocument, research_code)

    search_codes = sorted({row.search_code for row in source_queries})
    searches = await web_search_transfer.searches_by_codes(search_codes)
    results = await web_search_transfer.results_for_searches(search_codes)

    page_codes = sorted({row.page_code for row in sources} | {row.page_code for row in results})
    pages = await web_search_transfer.pages_by_codes(page_codes)

    with ArchiveWriter(path) as archive:
        archive.add_rows(ENTITY_PAGES, [row_to_json(row, omit=_BODY_OMITTED) for row in pages])
        archive.add_rows(ENTITY_SEARCHES, [row_to_json(row) for row in searches])
        archive.add_rows(
            ENTITY_SEARCH_RESULTS,
            [row_to_json(row, omit=_SURROGATE_ID_OMITTED) for row in results],
        )
        archive.add_rows(ENTITY_GROUP, [row_to_json(group)] if group is not None else [])
        archive.add_rows(ENTITY_RESEARCH, [row_to_json(research, omit=_BODY_OMITTED)])
        archive.add_rows(ENTITY_AREAS, [row_to_json(row, omit=_BODY_OMITTED) for row in areas])
        archive.add_rows(ENTITY_NOTES, [row_to_json(row, omit=_BODY_OMITTED) for row in notes])
        archive.add_rows(ENTITY_SOURCE_QUERIES, [row_to_json(row) for row in source_queries])
        archive.add_rows(ENTITY_SOURCES, [row_to_json(row) for row in sources])

        if research.body:
            archive.add_body(ENTITY_RESEARCH, research.code, research.body)
        for area in areas:
            if area.body:
                archive.add_body(ENTITY_AREAS, area.code, area.body)
        for note in notes:
            if note.body:
                archive.add_body(ENTITY_NOTES, note.code, note.body)
        for page in pages:
            if page.body is not None:
                archive.add_page_material(page.code, page.body)

        manifest = archive.finish(
            archive_id=str(ULID()),
            source=ManifestSource(
                install_id=await install_id(),
                app_version=app_version(),
                alembic_heads=await transfer_crud.alembic_heads(),
            ),
            roots=[
                ManifestRoot(
                    type=ENTITY_RESEARCH, code=research.code, title=research.title
                )
            ],
            counts={
                ENTITY_GROUP: 1 if group is not None else 0,
                ENTITY_RESEARCH: 1,
                ENTITY_AREAS: len(areas),
                ENTITY_NOTES: len(notes),
                ENTITY_SOURCE_QUERIES: len(source_queries),
                ENTITY_SEARCHES: len(searches),
                ENTITY_SEARCH_RESULTS: len(results),
                ENTITY_SOURCES: len(sources),
                ENTITY_PAGES: len(pages),
            },
            dangling_refs=_dangling_refs(
                research=research,
                group=group,
                areas=areas,
                notes=notes,
                source_queries=source_queries,
                sources=sources,
                searches=searches,
                pages=pages,
            ),
        )

    return ExportedArchive(
        path=path, file_name=archive_file_name(research.title, research.code), manifest=manifest
    )


def _dangling_refs(
    *,
    research,
    group,
    areas: list,
    notes: list,
    source_queries: list,
    sources: list,
    searches: list,
    pages: list,
) -> list[str]:
    """Ссылки из тел наружу архива — на сущности других исследований.

    Тянуть их по ссылке нельзя (так уехала бы половина реестра), вычищать из тел — тем более:
    вычищенная ссылка не оставляет следа. Поэтому они просто названы в манифесте.
    """
    present: set[tuple[str, str]] = {(RESEARCH_CODE_PREFIX, research.code)}
    if group is not None:
        present.add((GROUP_CODE_PREFIX, group.code))
    present |= {(AREA_CODE_PREFIX, row.code) for row in areas}
    present |= {(NOTE_CODE_PREFIX, row.code) for row in notes}
    present |= {(SOURCE_QUERY_CODE_PREFIX, row.code) for row in source_queries}
    present |= {(SOURCE_DOCUMENT_CODE_PREFIX, row.code) for row in sources}
    present |= {(SEARCH_CODE_PREFIX, row.code) for row in searches}
    present |= {(PAGE_CODE_PREFIX, row.code) for row in pages}

    mentioned: set[tuple[str, str]] = set()
    for text in _texts_with_references(
        research=research, group=group, areas=areas, notes=notes,
        source_queries=source_queries, sources=sources,
    ):
        mentioned |= collect_references(text)

    return sorted(f"{prefix}@{code}" for prefix, code in mentioned - present)


def _texts_with_references(
    *, research, group, areas: list, notes: list, source_queries: list, sources: list
) -> list[str]:
    """Тексты, которые писал агент, — только в них ссылка означает ссылку.

    Материал страниц и выдача движка сюда не входят: там ``SOURCE@`` с десятью hex-символами —
    совпадение в чужом тексте, а не ссылка на нашу сущность.
    """
    texts = [research.body, research.description]
    if group is not None:
        texts.append(group.description)
    for area in areas:
        texts += [area.body, area.description, area.objective, area.scope, area.expectations]
    for note in notes:
        texts += [note.body, note.description]
    for row in source_queries:
        texts.append(row.query)
    for row in sources:
        texts += [row.note, row.summary]
    return [text for text in texts if text]


__all__ = ["ExportedArchive", "RESEARCH_MODULE", "export_research", "install_id"]
