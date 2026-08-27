"""Константы research — размеры полей области + статусы документа + типы заметки.

Длины областей дублируются в модели (``String(n)``) и в CRUD-усечении (``_clip``).
Статус есть только у источника (``research_source_document``): его состояние в research-пайплайне
(целостность + решение об отсеве). У исследования/области/запроса статуса нет — артефакты
и таблица связей. ``DOC_STATUSES`` — единый источник для модели и миграции (``CHECK``).

``NOTE_KINDS`` — тип заметки (``research_note``): свободная рабочая память исследования, где
тип заставляет агента отделить вывод от наблюдения от гипотезы от вопроса («схема как промпт»).
Единый источник для модели и миграции (``CHECK``).
"""

from __future__ import annotations

# ── presentation code prefixes (граница, НЕ хранилище — см. research.codes) ──
# Хранимый код — голый 22-hex хеш; тип-слово надевается на выходе DTO (кодек дописывает
# разделитель `@` → на проводе `RESEARCH@<hash>`), снимается на входе. Значение = голое слово.
# research — единственный дом префиксов: свои сущности + web_search-коды, на которые ссылается
# (search/page); сам web_search коды не типизирует.
GROUP_CODE_PREFIX = "GROUP"
RESEARCH_CODE_PREFIX = "RESEARCH"
AREA_CODE_PREFIX = "AREA"
NOTE_CODE_PREFIX = "NOTE"
SOURCE_QUERY_CODE_PREFIX = "QUERY"
SOURCE_DOCUMENT_CODE_PREFIX = "SOURCE"
SEARCH_CODE_PREFIX = "SEARCH"  # web_search_query (референс из research)
PAGE_CODE_PREFIX = "PAGE"  # web_search_page (референс из research)

# Что делать с исследованиями полки при её удалении. Полка — раскладка, поэтому по умолчанию
# исследования переживают её (``detach``); остальные два варианта человек выбирает явно.
GROUP_RESEARCHES_DETACH = "detach"
GROUP_RESEARCHES_MOVE = "move"
GROUP_RESEARCHES_DELETE = "delete"
GROUP_RESEARCHES_ACTIONS = (
    GROUP_RESEARCHES_DETACH,
    GROUP_RESEARCHES_MOVE,
    GROUP_RESEARCHES_DELETE,
)

RESEARCH_TITLE_MAX = 128

GROUP_TITLE_MAX = 128
GROUP_DESCRIPTION_MAX = 512
GROUP_ICON_MAX = 64
GROUP_COLOR_MAX = 32
# Стартовая позиция группы. Ненулевая, чтобы новую группу можно было подвинуть и вверх,
# и вниз, не перенумеровывая соседей: больший sort = выше в списке.
GROUP_SORT_DEFAULT = 500

AREA_TITLE_MAX = 128
AREA_DESCRIPTION_MAX = 512
AREA_BRIEF_MAX = 1024  # objective / scope / expectations

DOC_ERROR = "error"
DOC_PENDING = "pending"
DOC_KEPT = "kept"
DOC_FILTERED = "filtered"
DOC_STATUSES = (DOC_ERROR, DOC_PENDING, DOC_KEPT, DOC_FILTERED)

NOTE_TITLE_MAX = 128
NOTE_DESCRIPTION_MAX = 512

NOTE_RESULT = "result"
NOTE_IDEA = "idea"
NOTE_QUESTION = "question"
NOTE_MEMORY = "memory"
NOTE_DECISION = "decision"
NOTE_CLARIFICATION = "clarification"
NOTE_KINDS = (
    NOTE_RESULT,
    NOTE_IDEA,
    NOTE_QUESTION,
    NOTE_MEMORY,
    NOTE_DECISION,
    NOTE_CLARIFICATION,
)


def sql_in(values: tuple[str, ...]) -> str:
    """Кортеж значений → строка для ``col IN (...)`` в CheckConstraint."""
    return ", ".join(f"'{value}'" for value in values)


__all__ = [
    "GROUP_CODE_PREFIX",
    "RESEARCH_CODE_PREFIX",
    "AREA_CODE_PREFIX",
    "NOTE_CODE_PREFIX",
    "SOURCE_QUERY_CODE_PREFIX",
    "SOURCE_DOCUMENT_CODE_PREFIX",
    "SEARCH_CODE_PREFIX",
    "PAGE_CODE_PREFIX",
    "RESEARCH_TITLE_MAX",
    "GROUP_TITLE_MAX",
    "GROUP_DESCRIPTION_MAX",
    "GROUP_ICON_MAX",
    "GROUP_COLOR_MAX",
    "GROUP_SORT_DEFAULT",
    "AREA_TITLE_MAX",
    "AREA_DESCRIPTION_MAX",
    "AREA_BRIEF_MAX",
    "DOC_ERROR",
    "DOC_PENDING",
    "DOC_KEPT",
    "DOC_FILTERED",
    "DOC_STATUSES",
    "NOTE_TITLE_MAX",
    "NOTE_DESCRIPTION_MAX",
    "NOTE_RESULT",
    "NOTE_IDEA",
    "NOTE_QUESTION",
    "NOTE_MEMORY",
    "NOTE_DECISION",
    "NOTE_CLARIFICATION",
    "NOTE_KINDS",
    "sql_in",
]
