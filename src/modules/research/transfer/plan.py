"""План импорта: карта кодов и решение по каждой записи — до единой записи в базу.

Порядок разбора совпадает с порядком записи (``ROW_ENTITIES``): сначала страницы и прогоны
поиска, потом реестр исследования. Так к моменту разбора дочерней таблицы код её родителя уже
решён, и естественный ключ считается по тем кодам, которые реально лягут в базу.

Опознание записи идёт по **неизменяемому**: времени создания и естественному ключу схемы.
Название и тело в сверке не участвуют — именно они меняются между выгрузкой и повторным
импортом, и опора на них превратила бы обновление правленого исследования в дубль.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.core.utils.date import datetime_from_agent
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
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.research.transfer.archive import ArchiveReader
from src.modules.research.transfer.constants import (
    ACTION_CREATE,
    ACTION_MERGE,
    ACTION_SKIP,
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
    IMPORT_MODE_ALWAYS,
    IMPORT_MODE_NEVER,
    IMPORT_MODE_NEWER,
    IMPORT_MODES,
    ROW_ENTITIES,
)
from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.manifest import Manifest
from src.modules.research.transfer.remap import assign_substitutes
from src.modules.research.transfer.rows import clip_to_columns, json_to_values, same_moment
from src.modules.web_search.constants import FETCH_STATUS_DONE
from src.modules.web_search.services import transfer as web_search_transfer

_ENTITY_MODEL = {
    ENTITY_GROUP: ResearchGroup,
    ENTITY_RESEARCH: Research,
    ENTITY_AREAS: ResearchArea,
    ENTITY_NOTES: ResearchNote,
    ENTITY_SOURCE_QUERIES: ResearchSourceQuery,
    ENTITY_SOURCES: ResearchSourceDocument,
}

_ENTITY_PREFIX = {
    ENTITY_GROUP: GROUP_CODE_PREFIX,
    ENTITY_RESEARCH: RESEARCH_CODE_PREFIX,
    ENTITY_AREAS: AREA_CODE_PREFIX,
    ENTITY_NOTES: NOTE_CODE_PREFIX,
    ENTITY_SOURCE_QUERIES: SOURCE_QUERY_CODE_PREFIX,
    ENTITY_SOURCES: SOURCE_DOCUMENT_CODE_PREFIX,
    ENTITY_SEARCHES: SEARCH_CODE_PREFIX,
    ENTITY_PAGES: PAGE_CODE_PREFIX,
}

_TITLE_FIELD = {
    ENTITY_GROUP: "title",
    ENTITY_RESEARCH: "title",
    ENTITY_AREAS: "title",
    ENTITY_NOTES: "title",
    ENTITY_SOURCE_QUERIES: "query",
    ENTITY_SOURCES: "summary",
    ENTITY_SEARCHES: "query",
    ENTITY_PAGES: "url",
}


@dataclass(frozen=True)
class Decision:
    """Что случится с одной записью архива и под каким кодом она ляжет."""

    origin: str
    code: str
    action: str
    title: str = ""

    @property
    def recoded(self) -> bool:
        return self.code != self.origin


@dataclass
class PlanWarnings:
    """То, о чём человек обязан узнать до нажатия кнопки."""

    dangling_refs: list[str] = field(default_factory=list)
    diverged_pages: list[dict[str, str]] = field(default_factory=list)
    locally_newer: list[dict[str, str]] = field(default_factory=list)
    truncated: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ImportPlan:
    """Полный план: строки архива, решения по ним и карта ссылок для подмены в телах."""

    manifest: Manifest
    mode: str
    same_install: bool
    rows: dict[str, list[dict[str, Any]]]
    decisions: dict[str, dict[str, Decision]]
    result_rows: list[dict[str, Any]]
    reference_map: dict[tuple[str, str], str]
    warnings: PlanWarnings

    def counts(self) -> dict[str, dict[str, int]]:
        summary: dict[str, dict[str, int]] = {}
        for entity in ROW_ENTITIES:
            decisions = self.decisions.get(entity, {}).values()
            summary[entity] = {
                ACTION_CREATE: sum(1 for d in decisions if d.action == ACTION_CREATE),
                ACTION_UPDATE: sum(1 for d in decisions if d.action == ACTION_UPDATE),
                ACTION_SKIP: sum(1 for d in decisions if d.action == ACTION_SKIP),
                ACTION_MERGE: sum(1 for d in decisions if d.action == ACTION_MERGE),
                "recode": sum(1 for d in decisions if d.recoded),
            }
        summary[ENTITY_SEARCH_RESULTS] = {
            ACTION_CREATE: len(self.result_rows),
            ACTION_UPDATE: 0,
            ACTION_SKIP: len(self.rows.get(ENTITY_SEARCH_RESULTS, [])) - len(self.result_rows),
            ACTION_MERGE: 0,
            "recode": 0,
        }
        return summary

    def details(self) -> dict[str, list[dict[str, str]]]:
        recoded = [
            {
                "entity": entity,
                "title": decision.title,
                "from": f"{_ENTITY_PREFIX[entity]}@{decision.origin}",
                "to": f"{_ENTITY_PREFIX[entity]}@{decision.code}",
            }
            for entity, decisions in self.decisions.items()
            for decision in decisions.values()
            if decision.recoded
        ]
        updating = [
            {
                "entity": entity,
                "title": decision.title,
                "code": f"{_ENTITY_PREFIX[entity]}@{decision.code}",
            }
            for entity, decisions in self.decisions.items()
            for decision in decisions.values()
            if decision.action == ACTION_UPDATE
        ]
        return {"recoded": recoded, "updating": updating}

    def root_codes(self) -> list[dict[str, str]]:
        research_decisions = self.decisions.get(ENTITY_RESEARCH, {})
        return [
            {
                "code": f"{RESEARCH_CODE_PREFIX}@{decision.code}",
                "title": decision.title,
            }
            for decision in research_decisions.values()
        ]


async def build_plan(reader: ArchiveReader, *, mode: str, install: str) -> ImportPlan:
    """Прочитать архив и решить судьбу каждой записи, не трогая базу на запись."""
    if mode not in IMPORT_MODES:
        raise ArchiveError(f"неизвестный режим импорта «{mode}»")

    manifest = reader.manifest or reader.open_manifest()
    rows = {entity: reader.rows(entity) for entity in ROW_ENTITIES}
    warnings = PlanWarnings(dangling_refs=list(manifest.dangling_refs))
    _collect_truncations(rows, warnings)

    decisions: dict[str, dict[str, Decision]] = {}
    decisions[ENTITY_PAGES] = await _plan_pages(rows[ENTITY_PAGES], warnings)
    decisions[ENTITY_SEARCHES] = await _plan_searches(
        rows[ENTITY_SEARCHES], mode=mode, archive_id=manifest.archive_id, warnings=warnings
    )
    for entity in (ENTITY_GROUP, ENTITY_RESEARCH, ENTITY_AREAS, ENTITY_NOTES):
        decisions[entity] = await _plan_owned(
            entity,
            rows[entity],
            decisions=decisions,
            mode=mode,
            archive_id=manifest.archive_id,
            warnings=warnings,
        )
    decisions[ENTITY_SOURCE_QUERIES] = await _plan_source_queries(
        rows[ENTITY_SOURCE_QUERIES],
        decisions=decisions,
        mode=mode,
        archive_id=manifest.archive_id,
        warnings=warnings,
    )
    decisions[ENTITY_SOURCES] = await _plan_sources(
        rows[ENTITY_SOURCES],
        decisions=decisions,
        mode=mode,
        archive_id=manifest.archive_id,
        warnings=warnings,
    )
    result_rows = await _plan_results(rows[ENTITY_SEARCH_RESULTS], decisions=decisions)
    _check_connectivity(rows, decisions)

    return ImportPlan(
        manifest=manifest,
        mode=mode,
        same_install=bool(manifest.source.install_id) and manifest.source.install_id == install,
        rows=rows,
        decisions=decisions,
        result_rows=result_rows,
        reference_map=_reference_map(decisions),
        warnings=warnings,
    )


def _decide_existing(mode: str, archived: datetime | None, local: datetime | None) -> str:
    """Запись опознана как наша — писать ли поверх."""
    if mode == IMPORT_MODE_NEVER:
        return ACTION_SKIP
    if mode == IMPORT_MODE_ALWAYS:
        return ACTION_UPDATE
    if archived is None or local is None:
        return ACTION_SKIP
    return ACTION_UPDATE if archived.replace(microsecond=0) > local.replace(microsecond=0) else ACTION_SKIP


def _moment(row: dict[str, Any], field_name: str) -> datetime | None:
    value = row.get(field_name)
    return datetime_from_agent(value) if value else None


def _title_of(entity: str, row: dict[str, Any]) -> str:
    return str(row.get(_TITLE_FIELD[entity]) or "")


async def _plan_pages(rows: list[dict[str, Any]], warnings: PlanWarnings) -> dict[str, Decision]:
    """Страницы сливаются, а не перевыпускаются: код страницы — хеш её url.

    Совпадение кода означает тот же адрес, то есть ту же страницу. Пустую или упавшую страницу
    заполняем материалом из архива, живую не трогаем: её материал уже разобран соседними
    исследованиями этой базы.
    """
    local = {page.code: page for page in await web_search_transfer.pages_by_codes(
        [row["code"] for row in rows]
    )}
    decisions: dict[str, Decision] = {}
    for row in rows:
        code = row["code"]
        title = _title_of(ENTITY_PAGES, row)
        page = local.get(code)
        if page is None:
            decisions[code] = Decision(origin=code, code=code, action=ACTION_CREATE, title=title)
            continue
        if page.url != row.get("url"):
            raise ArchiveError(
                f"страница {code} в архиве указывает на другой адрес, чем в базе — архиву верить нельзя"
            )
        archived_is_material = row.get("status") == FETCH_STATUS_DONE
        local_is_material = page.status == FETCH_STATUS_DONE
        if archived_is_material and not local_is_material:
            action = ACTION_MERGE
        else:
            action = ACTION_SKIP
            if archived_is_material and local_is_material and page.body_hash != row.get("body_hash"):
                warnings.diverged_pages.append({"code": code, "url": page.url})
        decisions[code] = Decision(origin=code, code=code, action=action, title=title)
    return decisions


async def _plan_searches(
    rows: list[dict[str, Any]], *, mode: str, archive_id: str, warnings: PlanWarnings
) -> dict[str, Decision]:
    """Прогон поиска опознаётся временем создания, текстом запроса и движком."""
    local = {row.code: row for row in await web_search_transfer.searches_by_codes(
        [row["code"] for row in rows]
    )}
    decisions: dict[str, Decision] = {}
    colliding: list[dict[str, Any]] = []
    for row in rows:
        code = row["code"]
        title = _title_of(ENTITY_SEARCHES, row)
        existing = local.get(code)
        if existing is None:
            decisions[code] = Decision(origin=code, code=code, action=ACTION_CREATE, title=title)
            continue
        same_record = (
            same_moment(existing.created_at, _moment(row, "created_at"))
            and existing.query == row.get("query")
            and existing.search_engine == row.get("search_engine")
        )
        if not same_record:
            colliding.append(row)
            continue
        action = _decide_existing(mode, _moment(row, "updated_at"), existing.updated_at)
        _note_locally_newer(warnings, ENTITY_SEARCHES, existing.code, title, mode, action, row, existing.updated_at)
        decisions[code] = Decision(origin=code, code=code, action=action, title=title)

    async def codes_in_use(candidates: list[str]) -> set[str]:
        return {row.code for row in await web_search_transfer.searches_by_codes(candidates)}

    substitutes = await assign_substitutes(
        archive_id=archive_id,
        origins=[row["code"] for row in colliding],
        codes_in_use=codes_in_use,
        reserved={decision.code for decision in decisions.values()},
    )
    for row in colliding:
        code = row["code"]
        decisions[code] = Decision(
            origin=code,
            code=substitutes[code],
            action=ACTION_CREATE,
            title=_title_of(ENTITY_SEARCHES, row),
        )
    return decisions


async def _plan_owned(
    entity: str,
    rows: list[dict[str, Any]],
    *,
    decisions: dict[str, dict[str, Decision]],
    mode: str,
    archive_id: str,
    warnings: PlanWarnings,
) -> dict[str, Decision]:
    """Группа, исследование, область и заметка: тождество по времени создания и родителю.

    У группы вместо родителя — название: полка это раскладка человека, и чужую полку с тем же
    кодом, но другим названием импорт переименовывать не вправе, он заводит свою.
    """
    model = _ENTITY_MODEL[entity]
    local = await transfer_crud.rows_by_codes(model, [row["code"] for row in rows])
    planned: dict[str, Decision] = {}
    colliding: list[dict[str, Any]] = []

    for row in rows:
        code = row["code"]
        title = _title_of(entity, row)
        existing = local.get(code)
        if existing is None:
            planned[code] = Decision(origin=code, code=code, action=ACTION_CREATE, title=title)
            continue
        if not _same_owned_record(entity, existing, row, decisions):
            colliding.append(row)
            continue
        action = _decide_existing(mode, _moment(row, "updated_at"), existing.updated_at)
        _note_locally_newer(warnings, entity, existing.code, title, mode, action, row, existing.updated_at)
        planned[code] = Decision(origin=code, code=code, action=action, title=title)

    async def codes_in_use(candidates: list[str]) -> set[str]:
        return await transfer_crud.codes_in_use(model, candidates)

    substitutes = await assign_substitutes(
        archive_id=archive_id,
        origins=[row["code"] for row in colliding],
        codes_in_use=codes_in_use,
        reserved={decision.code for decision in planned.values()},
    )
    for row in colliding:
        code = row["code"]
        planned[code] = Decision(
            origin=code,
            code=substitutes[code],
            action=ACTION_CREATE,
            title=_title_of(entity, row),
        )
    return planned


def _same_owned_record(
    entity: str, existing: Any, row: dict[str, Any], decisions: dict[str, dict[str, Decision]]
) -> bool:
    if not same_moment(existing.created_at, _moment(row, "created_at")):
        return False
    if entity == ENTITY_GROUP:
        return existing.title == row.get("title")
    if entity in (ENTITY_AREAS, ENTITY_NOTES):
        return existing.research_code == _mapped(decisions, ENTITY_RESEARCH, row.get("research_code"))
    return True


def _mapped(decisions: dict[str, dict[str, Decision]], entity: str, code: str | None) -> str | None:
    """Код, под которым запись архива ляжет в эту базу (или уже лежит)."""
    if code is None:
        return None
    decision = decisions.get(entity, {}).get(code)
    return decision.code if decision is not None else code


async def _plan_source_queries(
    rows: list[dict[str, Any]],
    *,
    decisions: dict[str, dict[str, Decision]],
    mode: str,
    archive_id: str,
    warnings: PlanWarnings,
) -> dict[str, Decision]:
    """Источниковый запрос опознаётся естественным ключом ``(область, прогон поиска)``.

    Ключ сильнее кода: он есть в схеме (``uq_research_source_query_area_search``) и работает
    даже тогда, когда код перевыпущен. Поэтому сначала спрашиваем про него, и только потом про
    занятость кода — иначе прерванный импорт добил бы себя нарушением уникальности.
    """
    area_codes = sorted({
        _mapped(decisions, ENTITY_AREAS, row.get("area_code")) for row in rows
    } - {None})
    local_rows = await transfer_crud.source_queries_by_areas(list(area_codes))
    by_pair = {(row.area_code, row.search_code): row for row in local_rows}
    by_code = await transfer_crud.rows_by_codes(
        ResearchSourceQuery, [row["code"] for row in rows]
    )

    planned: dict[str, Decision] = {}
    colliding: list[dict[str, Any]] = []
    for row in rows:
        code = row["code"]
        title = _title_of(ENTITY_SOURCE_QUERIES, row)
        pair = (
            _mapped(decisions, ENTITY_AREAS, row.get("area_code")),
            _mapped(decisions, ENTITY_SEARCHES, row.get("search_code")),
        )
        existing = by_pair.get(pair)
        if existing is not None:
            planned[code] = Decision(
                origin=code, code=existing.code, action=ACTION_SKIP, title=title
            )
            continue
        occupied = by_code.get(code)
        if occupied is None:
            planned[code] = Decision(origin=code, code=code, action=ACTION_CREATE, title=title)
            continue
        colliding.append(row)

    async def codes_in_use(candidates: list[str]) -> set[str]:
        return await transfer_crud.codes_in_use(ResearchSourceQuery, candidates)

    substitutes = await assign_substitutes(
        archive_id=archive_id,
        origins=[row["code"] for row in colliding],
        codes_in_use=codes_in_use,
        reserved={decision.code for decision in planned.values()},
    )
    for row in colliding:
        code = row["code"]
        planned[code] = Decision(
            origin=code,
            code=substitutes[code],
            action=ACTION_CREATE,
            title=_title_of(ENTITY_SOURCE_QUERIES, row),
        )
    return planned


async def _plan_sources(
    rows: list[dict[str, Any]],
    *,
    decisions: dict[str, dict[str, Decision]],
    mode: str,
    archive_id: str,
    warnings: PlanWarnings,
) -> dict[str, Decision]:
    """Источник опознаётся естественным ключом ``(источниковый запрос, страница)``."""
    query_codes = sorted({
        _mapped(decisions, ENTITY_SOURCE_QUERIES, row.get("query_code")) for row in rows
    } - {None})
    local_rows = await transfer_crud.source_documents_by_queries(list(query_codes))
    by_pair = {(row.query_code, row.page_code): row for row in local_rows}
    by_code = await transfer_crud.rows_by_codes(
        ResearchSourceDocument, [row["code"] for row in rows]
    )

    planned: dict[str, Decision] = {}
    colliding: list[dict[str, Any]] = []
    for row in rows:
        code = row["code"]
        title = _title_of(ENTITY_SOURCES, row)
        pair = (
            _mapped(decisions, ENTITY_SOURCE_QUERIES, row.get("query_code")),
            row.get("page_code"),
        )
        existing = by_pair.get(pair)
        if existing is not None:
            action = _decide_existing(mode, _moment(row, "updated_at"), existing.updated_at)
            _note_locally_newer(
                warnings, ENTITY_SOURCES, existing.code, title, mode, action, row, existing.updated_at
            )
            planned[code] = Decision(
                origin=code, code=existing.code, action=action, title=title
            )
            continue
        if by_code.get(code) is None:
            planned[code] = Decision(origin=code, code=code, action=ACTION_CREATE, title=title)
            continue
        colliding.append(row)

    async def codes_in_use(candidates: list[str]) -> set[str]:
        return await transfer_crud.codes_in_use(ResearchSourceDocument, candidates)

    substitutes = await assign_substitutes(
        archive_id=archive_id,
        origins=[row["code"] for row in colliding],
        codes_in_use=codes_in_use,
        reserved={decision.code for decision in planned.values()},
    )
    for row in colliding:
        code = row["code"]
        planned[code] = Decision(
            origin=code,
            code=substitutes[code],
            action=ACTION_CREATE,
            title=_title_of(ENTITY_SOURCES, row),
        )
    return planned


async def _plan_results(
    rows: list[dict[str, Any]], *, decisions: dict[str, dict[str, Decision]]
) -> list[dict[str, Any]]:
    """Строки выдачи: кода нет вовсе, опознание — только естественным ключом."""
    mapped_rows = [
        dict(row, query_code=_mapped(decisions, ENTITY_SEARCHES, row.get("query_code")))
        for row in rows
    ]
    existing = await web_search_transfer.result_pairs_for_searches(
        sorted({row["query_code"] for row in mapped_rows if row["query_code"]})
    )
    return [
        row for row in mapped_rows
        if (row["query_code"], row.get("page_code")) not in existing
    ]


def _note_locally_newer(
    warnings: PlanWarnings,
    entity: str,
    code: str,
    title: str,
    mode: str,
    action: str,
    row: dict[str, Any],
    local_updated_at: datetime | None,
) -> None:
    """Пропуск по умолчанию из-за более свежей местной правки — повод сказать об этом человеку."""
    if mode != IMPORT_MODE_NEWER or action != ACTION_SKIP:
        return
    archived = _moment(row, "updated_at")
    if archived is None or local_updated_at is None:
        return
    # Сравнение округляется до секунды по той же причине, по которой округляет решение
    # (``same_moment``): доли секунды есть только в базе, и без округления человек получил бы
    # список «местная копия свежее» из записей, совпадающих с архивом байт в байт.
    if archived.replace(microsecond=0) >= local_updated_at.replace(microsecond=0):
        return
    warnings.locally_newer.append(
        {"entity": entity, "code": f"{_ENTITY_PREFIX[entity]}@{code}", "title": title}
    )


def _collect_truncations(
    rows: dict[str, list[dict[str, Any]]], warnings: PlanWarnings
) -> None:
    for entity, model in _ENTITY_MODEL.items():
        for row in rows.get(entity, []):
            _, clipped = clip_to_columns(model, json_to_values(model, dict(row)))
            warnings.truncated += [
                {
                    "entity": entity,
                    "code": f"{_ENTITY_PREFIX[entity]}@{row.get('code', '')}",
                    "field": name,
                }
                for name in clipped
            ]


def _check_connectivity(
    rows: dict[str, list[dict[str, Any]]], decisions: dict[str, dict[str, Decision]]
) -> None:
    """Каждая ссылка внутри архива обязана попадать в сам архив.

    Экспорт это обеспечивает отбором, но архив приходит извне: источник без своей страницы даёт
    не «источник без материала», а битую ссылку в базе — и узнать об этом лучше до записи.
    """
    required = {
        ENTITY_SOURCES: (("page_code", ENTITY_PAGES), ("query_code", ENTITY_SOURCE_QUERIES),
                         ("area_code", ENTITY_AREAS), ("research_code", ENTITY_RESEARCH)),
        ENTITY_SOURCE_QUERIES: (("search_code", ENTITY_SEARCHES), ("area_code", ENTITY_AREAS),
                                ("research_code", ENTITY_RESEARCH)),
        ENTITY_SEARCH_RESULTS: (("query_code", ENTITY_SEARCHES), ("page_code", ENTITY_PAGES)),
        ENTITY_AREAS: (("research_code", ENTITY_RESEARCH),),
        ENTITY_NOTES: (("research_code", ENTITY_RESEARCH),),
        ENTITY_RESEARCH: (("group_code", ENTITY_GROUP),),
    }
    for entity, links in required.items():
        for row in rows.get(entity, []):
            for column, target in links:
                code = row.get(column)
                if code is None or code in decisions.get(target, {}):
                    continue
                raise ArchiveError(
                    f"архив внутренне противоречив: {entity}.{column} ссылается на {code}, "
                    f"которого в архиве нет"
                )


def _reference_map(
    decisions: dict[str, dict[str, Decision]]
) -> dict[tuple[str, str], str]:
    """``(тип, старый код) → новый код`` для подмены ссылок в телах."""
    return {
        (_ENTITY_PREFIX[entity], decision.origin): decision.code
        for entity, planned in decisions.items()
        for decision in planned.values()
    }


__all__ = ["Decision", "ImportPlan", "PlanWarnings", "build_plan"]
