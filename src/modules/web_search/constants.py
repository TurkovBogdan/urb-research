"""web_search: статусы таблиц (общий источник для моделей, миграций и CRUD).

Две роли модуля — два набора статусов с одинаковой машиной состояний
``pending → processing → done | error`` (ретраев/очереди нет — переход терминальный):
- ``SEARCH_STATUS_*`` — прогон поиска (``web_search_query``);
- ``FETCH_STATUS_*`` — получение контента страницы (``web_search_page``).
"""

from __future__ import annotations

# ── web_search_query (поиск) ─────────────────────────────────────────────────
SEARCH_STATUS_PENDING = "pending"  # создан, поиск ещё не начался
SEARCH_STATUS_PROCESSING = "processing"  # идёт поиск + получение контента страниц
SEARCH_STATUS_DONE = "done"  # выполнен (в том числе если результатов не нашлось)
SEARCH_STATUS_ERROR = "error"  # движок упал — терминально (без повторов)
SEARCH_STATUSES: tuple[str, ...] = (
    SEARCH_STATUS_PENDING,
    SEARCH_STATUS_PROCESSING,
    SEARCH_STATUS_DONE,
    SEARCH_STATUS_ERROR,
)

# ── web_search_page (получение контента) ─────────────────────────────────────
FETCH_STATUS_PENDING = "pending"  # страница создана, контент ещё не получен
FETCH_STATUS_PROCESSING = "processing"  # идёт получение контента
FETCH_STATUS_DONE = "done"  # контент получен и обработан
FETCH_STATUS_ERROR = "error"  # получение контента упало — терминально (без повторов)
FETCH_STATUSES: tuple[str, ...] = (
    FETCH_STATUS_PENDING,
    FETCH_STATUS_PROCESSING,
    FETCH_STATUS_DONE,
    FETCH_STATUS_ERROR,
)


def sql_in(values: tuple[str, ...]) -> str:
    """``('a', 'b')`` → ``"'a', 'b'"`` для CheckConstraint."""
    return ", ".join(f"'{v}'" for v in values)


__all__ = [
    "SEARCH_STATUS_PENDING",
    "SEARCH_STATUS_PROCESSING",
    "SEARCH_STATUS_DONE",
    "SEARCH_STATUS_ERROR",
    "SEARCH_STATUSES",
    "FETCH_STATUS_PENDING",
    "FETCH_STATUS_PROCESSING",
    "FETCH_STATUS_DONE",
    "FETCH_STATUS_ERROR",
    "FETCH_STATUSES",
    "sql_in",
]
