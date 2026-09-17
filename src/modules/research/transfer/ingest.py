"""Применение плана: запись строк в базу и подмена ссылок в телах.

Порядок — от независимых таблиц к зависимым, транзакция на шаг. Частичная запись после обрыва
не страшна: повторный запуск того же архива строит ту же карту (код подмены выводится, а не
бросается) и узнаёт свои же записи по неизменяемым признакам, поэтому дописывает недостающее
вместо второго комплекта.

Ссылки в телах переписываются **на записи**, а не вторым проходом: иначе база какое-то время
держала бы ссылки, ведущие не туда, и все тела пришлось бы писать дважды.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.modules.research.crud import transfer as transfer_crud
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.research.transfer.archive import ArchiveReader
from src.modules.research.transfer.constants import (
    ACTION_CREATE,
    ACTION_MERGE,
    ACTION_UPDATE,
    ENTITY_AREAS,
    ENTITY_GROUP,
    ENTITY_NOTES,
    ENTITY_PAGES,
    ENTITY_RESEARCH,
    ENTITY_SEARCHES,
    ENTITY_SEARCH_RESULTS,
    ENTITY_SOURCES,
    ENTITY_SOURCE_QUERIES,
)
from src.modules.research.transfer.plan import Decision, ImportPlan
from src.modules.research.transfer.refs import rewrite_references
from src.modules.research.transfer.rows import clip_to_columns, json_to_values
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.models.query_result import WebSearchQueryResult
from src.modules.web_search.services import transfer as web_search_transfer

# Поля, в которых ссылку писал агент. Материал страниц и выдача движка сюда не входят намеренно:
# там ``SOURCE@`` с десятью hex-символами — совпадение в чужом тексте, а не ссылка.
_TEXTS_WITH_REFERENCES = {
    ENTITY_GROUP: ("description",),
    ENTITY_RESEARCH: ("body", "description"),
    ENTITY_AREAS: ("body", "description", "objective", "scope", "expectations"),
    ENTITY_NOTES: ("body", "description"),
    ENTITY_SOURCE_QUERIES: ("query",),
    ENTITY_SOURCES: ("note", "summary"),
}

_ENTITY_MODEL = {
    ENTITY_GROUP: ResearchGroup,
    ENTITY_RESEARCH: Research,
    ENTITY_AREAS: ResearchArea,
    ENTITY_NOTES: ResearchNote,
    ENTITY_SOURCE_QUERIES: ResearchSourceQuery,
    ENTITY_SOURCES: ResearchSourceDocument,
}

_PARENT_FIELDS = {
    ENTITY_RESEARCH: {"group_code": ENTITY_GROUP},
    ENTITY_AREAS: {"research_code": ENTITY_RESEARCH},
    ENTITY_NOTES: {"research_code": ENTITY_RESEARCH},
    ENTITY_SOURCE_QUERIES: {
        "research_code": ENTITY_RESEARCH,
        "area_code": ENTITY_AREAS,
        "search_code": ENTITY_SEARCHES,
    },
    ENTITY_SOURCES: {
        "research_code": ENTITY_RESEARCH,
        "area_code": ENTITY_AREAS,
        "query_code": ENTITY_SOURCE_QUERIES,
    },
}

_BODY_ENTITIES = (ENTITY_RESEARCH, ENTITY_AREAS, ENTITY_NOTES)


@dataclass
class ImportReport:
    """Что импорт сделал с базой — то же, что обещал план, но фактом."""

    roots: list[dict[str, str]] = field(default_factory=list)
    counts: dict[str, dict[str, int]] = field(default_factory=dict)
    refs_rewritten: int = 0
    dangling_refs: list[str] = field(default_factory=list)
    truncated: list[dict[str, str]] = field(default_factory=list)


async def apply_plan(reader: ArchiveReader, plan: ImportPlan) -> ImportReport:
    """Записать всё, что решено планом, и вернуть отчёт."""
    report = ImportReport(
        roots=plan.root_codes(), dangling_refs=list(plan.warnings.dangling_refs)
    )

    report.counts[ENTITY_PAGES] = await _apply_pages(reader, plan)
    report.counts[ENTITY_SEARCHES] = await _apply_searches(plan)
    report.counts[ENTITY_SEARCH_RESULTS] = await _apply_results(plan)
    for entity in (
        ENTITY_GROUP,
        ENTITY_RESEARCH,
        ENTITY_AREAS,
        ENTITY_NOTES,
        ENTITY_SOURCE_QUERIES,
        ENTITY_SOURCES,
    ):
        report.counts[entity] = await _apply_owned(entity, reader, plan, report)
    return report


def _tally() -> dict[str, int]:
    return {"created": 0, "updated": 0, "skipped": 0, "merged": 0}


async def _apply_pages(reader: ArchiveReader, plan: ImportPlan) -> dict[str, int]:
    """Страницы: новые — целиком с материалом, пустые и упавшие — дозаполняются."""
    tally = _tally()
    fresh: list[dict[str, Any]] = []
    for row in plan.rows[ENTITY_PAGES]:
        decision = plan.decisions[ENTITY_PAGES][row["code"]]
        if decision.action == ACTION_CREATE:
            values = json_to_values(WebSearchPage, dict(row))
            values["body"] = reader.page_material(row["code"])
            fresh.append(values)
            tally["created"] += 1
        elif decision.action == ACTION_MERGE:
            await web_search_transfer.page_fill_material(
                decision.code,
                body=reader.page_material(row["code"]),
                body_hash=row.get("body_hash"),
                status=row["status"],
                fetch_engine=row.get("fetch_engine"),
                fetched_at=json_to_values(WebSearchPage, dict(row))["fetched_at"],
                error=row.get("error"),
            )
            tally["merged"] += 1
        else:
            tally["skipped"] += 1
    await web_search_transfer.pages_insert(fresh)
    return tally


async def _apply_searches(plan: ImportPlan) -> dict[str, int]:
    tally = _tally()
    fresh: list[dict[str, Any]] = []
    for row in plan.rows[ENTITY_SEARCHES]:
        decision = plan.decisions[ENTITY_SEARCHES][row["code"]]
        values = json_to_values(WebSearchQuery, dict(row))
        values["code"] = decision.code
        if decision.action == ACTION_CREATE:
            fresh.append(values)
            tally["created"] += 1
        elif decision.action == ACTION_UPDATE:
            await web_search_transfer.search_replace(
                decision.code, {k: v for k, v in values.items() if k != "code"}
            )
            tally["updated"] += 1
        else:
            tally["skipped"] += 1
    await web_search_transfer.searches_insert(fresh)
    return tally


async def _apply_results(plan: ImportPlan) -> dict[str, int]:
    """Строки выдачи вставляются без суррогатного ключа — его выдаёт принимающая база."""
    rows = [
        json_to_values(WebSearchQueryResult, dict(row), omit=("id",))
        for row in plan.result_rows
    ]
    await web_search_transfer.results_insert(rows)
    tally = _tally()
    tally["created"] = len(rows)
    tally["skipped"] = len(plan.rows[ENTITY_SEARCH_RESULTS]) - len(rows)
    return tally


async def _apply_owned(
    entity: str, reader: ArchiveReader, plan: ImportPlan, report: ImportReport
) -> dict[str, int]:
    """Собственные таблицы research: коды подменяются, тела переписываются, ссылки переезжают."""
    model = _ENTITY_MODEL[entity]
    tally = _tally()
    fresh: list[dict[str, Any]] = []

    for row in plan.rows[entity]:
        decision = plan.decisions[entity][row["code"]]
        if decision.action not in (ACTION_CREATE, ACTION_UPDATE):
            tally["skipped"] += 1
            continue

        values = _values_for(entity, row, reader, plan, decision, report)
        if decision.action == ACTION_CREATE:
            fresh.append(values)
            tally["created"] += 1
        else:
            await transfer_crud.replace_row(
                model, decision.code, {k: v for k, v in values.items() if k != "code"}
            )
            tally["updated"] += 1

    await transfer_crud.insert_rows(model, fresh)
    return tally


def _values_for(
    entity: str,
    row: dict[str, Any],
    reader: ArchiveReader,
    plan: ImportPlan,
    decision: Decision,
    report: ImportReport,
) -> dict[str, Any]:
    model = _ENTITY_MODEL[entity]
    values = json_to_values(model, dict(row))
    values["code"] = decision.code

    for column, parent_entity in _PARENT_FIELDS.get(entity, {}).items():
        values[column] = _mapped_code(plan, parent_entity, values.get(column))

    if entity in _BODY_ENTITIES:
        values["body"] = reader.body(entity, decision.origin)

    for column in _TEXTS_WITH_REFERENCES[entity]:
        rewritten, count = rewrite_references(values.get(column), plan.reference_map)
        values[column] = rewritten
        report.refs_rewritten += count

    values, clipped = clip_to_columns(model, values)
    report.truncated += [
        {"entity": entity, "code": decision.code, "field": name} for name in clipped
    ]
    return values


def _mapped_code(plan: ImportPlan, entity: str, code: str | None) -> str | None:
    if code is None:
        return None
    decision = plan.decisions.get(entity, {}).get(code)
    return decision.code if decision is not None else code


__all__ = ["ImportReport", "apply_plan"]
