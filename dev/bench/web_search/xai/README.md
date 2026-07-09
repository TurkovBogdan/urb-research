# Верстак xAI (web_search)

Отработка движка поиска xAI (Grok) в том виде, в каком его использует модуль `web_search` —
через провайдер-адаптер `providers/xai::XaiSearchEngine`, а не сырой коннектор. Ключ и тумблер
берутся из runtime-настроек `core_connectors`. Сырой результат складывается в `tmp/search.json`.

Отличие от tavily/firecrawl-бенчей: у xAI **нет** raw search-эндпойнта. «Поиск» — это
агентский вызов `responses()` коннектора с server-side инструментом `web_search` + строгий JSON
(`LINKS_SCHEMA`). Модель сама ранжирует найденное; адаптер оставляет только заземлённые
ссылки (URL, реально встреченные в `web_search_call.action.sources`). Сырой коннектор (без
доменного маппинга) — отдельный бенч `dev/bench/core_connectors/xai`.

## Запуск

```bash
uv run python -m dev.bench.web_search.xai.run_search   # заземлённые ссылки + summary/reason
```

## Что возвращает `XaiSearchEngine.search(request)`

Список ссылок в общем для движков формате:

```
{url, rank, score, summary, title, meta: {reason}}
```

- `score` — `relevance` (0–1), которую проставила модель.
- `summary` — **краткое содержание** страницы в контексте запроса (2–3 предложения),
  поле строгого вывода; кладётся в колонку `web_search_query_result.summary`.
- `title` — заголовок документа; кладётся в колонку `web_search_page.title` (свойство
  страницы, не запроса).
- `meta.reason` — почему ссылка релевантна (обоснование модели).

Grok — **только** движок поиска (роль `SearchEngine`), контент страниц он не отдаёт: тело
доскрейпит движок контента (`fetch_engine`).

## Гранёные углы

- URL печатает **сама модель** → адаптер отбрасывает невстреченные поиском (защита от
  галлюцинированных ссылок). Заземление проверяет бенч
  `dev/bench/core_connectors/xai/verify_relevant_links.py`.
- `time_range` xAI web_search не поддерживает — движок его опускает.
- Домены: `include_domains` → `allowed_domains` (≤5) **или** `exclude_domains` →
  `excluded_domains`; xAI не принимает оба сразу.

Артефакт прогона — `tmp/search.json`.
