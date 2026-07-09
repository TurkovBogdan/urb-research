"""Провайдер-агностичная модель запроса поиска.

Заполняем общие поля (что хотим от поиска), а каждый провайдер интерпретирует те,
которые понимает (остальные игнорирует). ``query`` → ``web_search_query.query``; все
остальные поля (``max_results``, домены, свежесть) складываются в ``web_search_query.params``
через ``to_params()``. Обратно из строки БД собирается ``from_stored`` (задача поиска).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_DEFAULT_MAX_RESULTS = 5


@dataclass(frozen=True)
class SearchRequest:
    query: str
    max_results: int = _DEFAULT_MAX_RESULTS
    include_domains: tuple[str, ...] = ()
    exclude_domains: tuple[str, ...] = ()
    time_range: str | None = None  # day | week | month | year (свежесть), если движок поддерживает

    def to_params(self) -> dict[str, Any]:
        """Поля запроса (кроме ``query``) для ``web_search_query.params`` — вкл. ``max_results``."""
        params: dict[str, Any] = {"max_results": self.max_results}
        if self.include_domains:
            params["include_domains"] = list(self.include_domains)
        if self.exclude_domains:
            params["exclude_domains"] = list(self.exclude_domains)
        if self.time_range:
            params["time_range"] = self.time_range
        return params

    @classmethod
    def from_stored(cls, query: str, params: Mapping[str, Any] | None) -> "SearchRequest":
        """Собрать запрос из строки БД (``query`` + ``params``, включая ``max_results``)."""
        params = params or {}
        return cls(
            query=query,
            max_results=params.get("max_results", _DEFAULT_MAX_RESULTS),
            include_domains=tuple(params.get("include_domains", ())),
            exclude_domains=tuple(params.get("exclude_domains", ())),
            time_range=params.get("time_range"),
        )


__all__ = ["SearchRequest"]
