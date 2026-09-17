"""Константы формата ``.urch`` — имена записей архива, пределы разбора, решения плана.

Единый источник для писателя архива, читателя и плана импорта: расхождение любой из этих
строк между экспортом и импортом означает архив, который не читается собственным приложением.
"""

from __future__ import annotations

ARCHIVE_EXTENSION = ".urch"
ARCHIVE_MEDIA_TYPE = "application/vnd.uroboros.research+zip"
ARCHIVE_FORMAT = "uroboros.research"

# Версия отвечает на один вопрос: сумеет ли ЭТА сборка прочитать ЭТОТ файл. Растёт только
# тогда, когда старый читатель разобрал бы файл неправильно, — прибавка колонки в строках
# терпится обеими сторонами и номер не двигает.
ARCHIVE_FORMAT_VERSION = 1

MIMETYPE_ENTRY = "mimetype"
MANIFEST_ENTRY = "manifest.json"

ENTITY_GROUP = "group"
ENTITY_RESEARCH = "research"
ENTITY_AREAS = "areas"
ENTITY_NOTES = "notes"
ENTITY_SOURCE_QUERIES = "source_queries"
ENTITY_SEARCHES = "searches"
ENTITY_SEARCH_RESULTS = "search_results"
ENTITY_SOURCES = "sources"
ENTITY_PAGES = "pages"

# Порядок = порядок записи в базу: от независимых таблиц к зависимым, чтобы ни одна ссылка
# не указывала в пустоту даже в середине прогона.
ROW_ENTITIES = (
    ENTITY_PAGES,
    ENTITY_SEARCHES,
    ENTITY_SEARCH_RESULTS,
    ENTITY_GROUP,
    ENTITY_RESEARCH,
    ENTITY_AREAS,
    ENTITY_NOTES,
    ENTITY_SOURCE_QUERIES,
    ENTITY_SOURCES,
)

BODY_DIRECTORY = {
    ENTITY_RESEARCH: "bodies/research",
    ENTITY_AREAS: "bodies/areas",
    ENTITY_NOTES: "bodies/notes",
}
PAGE_MATERIAL_DIRECTORY = "pages"


def rows_entry(entity: str) -> str:
    return f"rows/{entity}.jsonl"


def body_entry(entity: str, code: str) -> str:
    return f"{BODY_DIRECTORY[entity]}/{code}.md"


def page_material_entry(code: str) -> str:
    return f"{PAGE_MATERIAL_DIRECTORY}/{code}.md"


# Пределы разбора недоверенного архива. Константы, а не настройки: настройка тут была бы
# приглашением поднять предел вместо того, чтобы разобраться, почему архив распух.
MAX_UPLOAD_BYTES = 512 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
MAX_ENTRY_BYTES = 64 * 1024 * 1024

# Что делать с записью, которая в базе уже есть.
IMPORT_MODE_NEWER = "newer"
IMPORT_MODE_ALWAYS = "always"
IMPORT_MODE_NEVER = "never"
IMPORT_MODES = (IMPORT_MODE_NEWER, IMPORT_MODE_ALWAYS, IMPORT_MODE_NEVER)

# Решение плана по одной записи.
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_SKIP = "skip"
ACTION_MERGE = "merge"
ACTIONS = (ACTION_CREATE, ACTION_UPDATE, ACTION_SKIP, ACTION_MERGE)

INSTALL_ID_KEY = "install_id"

__all__ = [
    "ACTIONS",
    "ACTION_CREATE",
    "ACTION_MERGE",
    "ACTION_SKIP",
    "ACTION_UPDATE",
    "ARCHIVE_EXTENSION",
    "ARCHIVE_FORMAT",
    "ARCHIVE_FORMAT_VERSION",
    "ARCHIVE_MEDIA_TYPE",
    "BODY_DIRECTORY",
    "ENTITY_AREAS",
    "ENTITY_GROUP",
    "ENTITY_NOTES",
    "ENTITY_PAGES",
    "ENTITY_RESEARCH",
    "ENTITY_SEARCHES",
    "ENTITY_SEARCH_RESULTS",
    "ENTITY_SOURCES",
    "ENTITY_SOURCE_QUERIES",
    "IMPORT_MODES",
    "IMPORT_MODE_ALWAYS",
    "IMPORT_MODE_NEVER",
    "IMPORT_MODE_NEWER",
    "INSTALL_ID_KEY",
    "MANIFEST_ENTRY",
    "MAX_ENTRY_BYTES",
    "MAX_TOTAL_UNCOMPRESSED_BYTES",
    "MAX_UPLOAD_BYTES",
    "MIMETYPE_ENTRY",
    "PAGE_MATERIAL_DIRECTORY",
    "ROW_ENTITIES",
    "body_entry",
    "page_material_entry",
    "rows_entry",
]
