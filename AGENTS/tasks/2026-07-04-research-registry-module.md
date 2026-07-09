---
title: research_registry module — stub + incremental build-out
date: 2026-07-04
status: in-work  # in-work | completed | deferred
description: "New domain module research_registry — the research orchestrator + registry that ships the research MCP server on top of a full web interface (MCP is a thin adapter over the same CRUD). Step 1: empty stub module registered in build_modules. Data model / CRUD / services / api / mcp added layer by layer later."
tags: [research_registry, research, mcp]
---

## Task

«Создавай болванку модуля research_registry» — начать модуль-оркестратор ресёрча
пустой болванкой, наращивать послойно (паттерн core_gateway / conversation_insights).

## Context

Дом ресёрч-пайплайна выбран: доменный модуль **`research_registry`**
(`2026-06-27-research-pipeline-design`). Владеет реестром
`Исследование → Запросы → Отчёт по запросу → Документы` + оркестрацией; потребляет
`web_content` (поиск/контент) и `core_gateway` (внешние API), сам сеть не трогает.

Архитектурный эталон — `AGENTS/semaphore-core/.../conversation_insights`: слоёный
модуль (models → migrations → crud → dto → services → agents), поверх два тонких
интерфейса-сиблинга над ОДНИМ CRUD — web (`api.py::internal_router`, `@guard`,
HTTPException) и MCP (`mcp/` → `mcp_server`, `@mcp.tool()`, ValueError, docstrings=
контракт для агента). MCP ничего не владеет, «идёт сверху». Регистрация MCP —
декларативная + ленивая (`mcp_servers = {"code": mcp_server}`, значение = функция-
конструктор → воркер чист).

Run-модель: один процесс `--backend --worker` держит HTTP + планировщик + MCP;
MCP монтируется в ту же FastAPI под `/mcp/<code>` при `SERVER_ENABLED` (не флаг —
декларативно из модуля). Блокер до первого MCP-сервера: `_collect_resolver`
требует ровно один `mcp_token_resolver` — решено дать статичный токен в ENV-
настройках ядра.

## What was done

Шаг 1 — болванка:
- `src/modules/research_registry/{__init__,module.py}` — `ResearchRegistryModule(Module)`,
  только `name = "research_registry"`; ни таблиц, ни миграций, ни роутеров, ни задач,
  ни MCP (добавляются послойно).
- Зарегистрирован в `apps/app/modules.py::build_modules` (после web_content).

## Result

Шаг 1 (болванка) готов: `__init__.py` + `module.py` (только `name`), зарегистрирован
в `build_modules`.

Шаг 2 (черновой сквозной MCP по схеме канвасов) готов и проверен:
- **models/** — `research` → `research_query` (FK) → `research_document` (FK,
  `url`/`title`/`page_code`/`relevance`/`summary`) + `research_report` (FK, markdown).
  Мягкие cross-module ссылки (без FK): `research_query.search_id`→`web_content_search`,
  `research_document.page_code`→`web_content_page`. `constants.py` — статусы + CHECK.
- **crud/** — research/query/document/report, каждая функция владеет `session_scope`.
- **dto.py** — `Research/Query/Document/ReportRow` + `ReportView` (отчёт + исходники).
- **mcp/** — сервер `research-registry`, 3 поверхности (тонкие адаптеры над CRUD),
  11 тулов: research_start/add_queries/queries/list/get · query_documents/document_add/
  set_relevance/set_summary · report_build/report_get. `_INSTRUCTIONS` = контракт агента.
- **MCP-auth блокер снят:** `Config.mcp_token` (ENV, пусто=allow-all dev) + черновой
  резолвер `mcp/auth.py`, модуль отдаёт как `mcp_token_resolver` → `_collect_resolver`
  не падает.
- **module.py** — `mcp_servers = {"research-registry": mcp_server}` (значение=функция,
  fastmcp не тянется в build_modules), `mcp_token_resolver`, импорт `models`.

Проверки:
- Смоук: `create_app` (server on, sqlite `:memory:`) монтирует `/mcp/research-registry`;
  in-memory `Client` прогнал весь поток (research→queries→doc→relevance/summary→
  report→report_get с 1 исходником). Схема dev — `create_all` из моделей.
- `uv run pytest --core` — **266 passed**. `migrate check` — up to date (миграций нет).

Изменено вне модуля: `src/apps/app/modules.py` (регистрация), `src/core/config.py`
(`mcp_token`).

Шаг 3 (web-вьюер: backend read-API + Vue-фича) готов и проверен:
- **backend** — `dto.py` расширен (`SqlDateTime` под фронт-парсер, `Paged`,
  `ResearchListRow`/`ResearchDetail`/`QueryDetail`); crud-хелперы
  (`research_list_paged`/`research_count`, `query_count_by_research_ids`); `api.py`
  (`internal_router`, prefix `/research`): `GET /researches` (пагинация+фильтр
  тема/статус/сорт, +query_count), `/researches/{id}` (с запросами), `/queries/{id}`
  (документы+отчёт). Подключён в `module.py`.
- **frontend** `web/src/features/research_registry/` — api.ts, labels.ts (цвета
  статусов), routes.ts, 3 store (researches/research-detail/query-detail), 3 view
  (ResearchesView список→ResearchView запросы→QueryView документы+markdown-отчёт),
  locales/ru.json. Роут подключён (`router/index.ts`), пункт «Исследования» в
  сайдбар (раздел «Данные», `IconTelescope`).
- Смоук: read-API через ASGITransport (список+query_count, SQL-даты, детали,
  404) поверх данных, засеянных MCP-тулами. vue-tsc 0, `--core` 266 passed,
  `web/dist` пересобран.

Шаг 4 (отсеянные материалы) готов и проверен:
- Модель `research_document` +`filtered` (Boolean, default False) +`filter_reason` (Text).
  Dev-схема применена пересозданием таблиц (seed-скрипт сносит только research_* +
  create_all — dev одноразовый).
- DTO `ResearchDocumentRow` +`filtered`/`filter_reason`; `document_list_by_query`
  сортирует kept-first (`filtered asc`, затем relevance). CRUD `document_set_filtered`.
- MCP: тулы `document_filter(id, reason)` / `document_keep(id)`; `query_documents`
  возвращает ВСЕ (kept + отсеянные); инструкции сервера обновлены.
- Фронт `QueryView`: секция «Документы» (релевантные) + отдельная «Отсеянные
  материалы» (пунктирная карточка, приглушённые, с причиной); store `keptDocuments`/
  `filteredDocuments`; локали `filtered`/`filter_reason`.
- Смоук: MCP `document_filter` + read-API отдаёт `filtered`/reason kept-first; vue-tsc 0,
  `--core` 266, `web/dist` пересобран. Seed обновлён (по 4 релевантных + отсеянные 2/1/1
  с причинами), стал идемпотентным.

Шаг 5 (открытие документа по клику) готов: `QueryView` — вся строка документа
(`VListItem :href=url target=_blank`) открывает источник в новой вкладке (tooltip
«Открыть источник», иконка `IconExternalLink` подсвечивается на hover); убрана
вложенная `<a>`; применено к «Документам» и «Отсеянным». Локаль `open_document`.
vue-tsc OK, dist пересобран. На будущее: при заполненном `page_code` клик сможет
вести во внутренний просмотр контента (`web_content_page`) вместо внешнего URL.

Шаг 6 (общий отчёт по исследованию) готов: модель `research` +`overview` (Text,
markdown с выводами, привязан к самому исследованию). DTO — `overview` в
`ResearchDetail` + компактный `ResearchOverview`; **в списке (`ResearchListRow`)
overview НЕТ** (не раздуваем выдачу). CRUD `research_set_overview`; MCP-тулы
`research_set_overview` / `research_get_overview` (+ инструкции сервера). Фронт
`ResearchView` — секция «Общий отчёт» (MarkdownRenderer) над списком запросов +
плейсхолдер, локали `overview`/`no_overview`, api.ts `ResearchDetail.overview`.
Seed пишет обзор с выводами (research_set_overview, 1809 симв.). Смоук: MCP set/get
+ read-API detail отдаёт overview, list — нет; vue-tsc OK, `--core` 266, dist пересобран.

Шаг 7 (открытие документа = наша страница; url — отдельная кнопка) готов:
- Модель `research_document` +`content` (Text, markdown — сохранённый материал, рендерим
  у себя). DTO — `content` только в новом `ResearchDocumentDetail` (список `documents`
  в QueryDetail остаётся лёгким, без content). CRUD `document_set_content`; MCP-тулы
  `document_set_content` / `document_get`(→detail с content) + инструкции сервера;
  read-API `GET /research/documents/{id}` → `ResearchDocumentDetail`.
- Фронт: роут `/research/documents/:id` + `DocumentView` (рендер `content` через
  MarkdownRenderer, метаданные, кнопка «Открыть источник»; при пустом content —
  плейсхолдер). `QueryView`: клик по строке документа → внутренняя деталка
  (`openDocument`), внешний URL — отдельная icon-кнопка `@click.stop`. Стор
  `document-detail.store`, api.ts `getDocument`/`ResearchDocumentDetail`.
- Локали: `document.detail.*`, `query.detail.open_source`; **фикс прошлого шага** —
  добавлены забытые `research.detail.overview`/`no_overview` (секция показывала сырой ключ).
- Seed: `CONTENTS` по URL → 12 kept-документов с сохранённым контентом, 4 отсеянных без
  (в реале их не скрейпят). Смоук: `/documents/{id}` отдаёт content, список — нет;
  vue-tsc OK, `--core` 266, dist пересобран.

## Next (layers, incremental)

- services/ — реальная оркестрация (план подзапросов → web_content поиск/контент →
  классификация → синтез отчёта; сейчас report_build/document_add принимают данные вручную).
- Тесты модуля (`tests/modules/research_registry/`): crud + api + mcp (in-memory Client).
- migrations/ — при стабилизации схемы (`rr`-abbr, по таблице на миграцию).
- Полноценный auth-модуль заберёт роль `mcp_token_resolver` (сейчас черновой на research_registry).
