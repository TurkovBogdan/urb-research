"""Прогон движка поиска xAI (``XaiSearchEngine``) из web_search: что отдаёт адаптер модуля.

В отличие от tavily/firecrawl у xAI нет raw search-эндпойнта — «поиск» это агентский
``responses()`` коннектора + строгий JSON. Здесь гоняем сам провайдер-адаптер модуля
(``providers/xai``): по запросу он возвращает заземлённые ссылки ``{url, rank, score,
summary, title, meta:{reason}}``. Фокус — поля ``summary`` (краткое содержание в контексте
запроса) и ``title`` (заголовок документа) + заземление URL. Ключ/тумблер xAI — из
runtime-настроек ``core_connectors``.

    uv run python -m dev.bench.web_search.xai.run_search
"""

from __future__ import annotations

import asyncio
import json

from dev.bench.core_connectors.xai.bootstrap import load_gateway_store
from dev.bench.web_search.xai.constants import MAX_RESULTS, OUT_DIR, SEARCH_QUERY
from src.core.database import close_database
from src.modules.web_search.providers.request import SearchRequest
from src.modules.web_search.providers.xai import XaiSearchEngine


async def main() -> None:
    await load_gateway_store()
    engine = XaiSearchEngine()
    request = SearchRequest(query=SEARCH_QUERY, max_results=MAX_RESULTS)
    try:
        results = await engine.search(request)
    finally:
        await close_database()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "search.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"query: {SEARCH_QUERY}")
    print(f"заземлённых ссылок: {len(results)}\n")
    for result in results:
        meta = result.get("meta") or {}
        summary = result.get("summary") or ""
        print(f"  {result.get('rank')}. score={result.get('score')} | {result.get('title') or ''}")
        print(f"     url: {result.get('url')}")
        print(f"     summary[{len(summary)}]: {summary[:200]}")
        print(f"     reason: {(meta.get('reason') or '')[:160]}")
    print(f"\nsaved: {path}")


if __name__ == "__main__":
    asyncio.run(main())
