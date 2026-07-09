"""web_search — модуль поиска в вебе и сохранения найденных страниц.

Зона ответственности: поиск в вебе через движки (Tavily, Firecrawl, …) + сохранение
контента найденных страниц (markdown, дедуп по url). Тройка таблиц:
``web_search_query`` → ``web_search_query_result`` → ``web_search_page``. Токены провайдеров
живут в модуле ``core_connectors`` (коннекторы владеют кредами).
"""

from src.modules.web_search.module import WebSearchModule

__all__ = ["WebSearchModule"]
