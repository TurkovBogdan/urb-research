"""ORM-модели web_search. Импорт регистрирует таблицы в ``Base.metadata``."""

from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.models.query_result import WebSearchQueryResult

__all__ = ["WebSearchPage", "WebSearchQuery", "WebSearchQueryResult"]
