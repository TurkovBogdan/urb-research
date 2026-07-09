---
title: web_content viewer UI (searches + pages)
date: 2026-07-01
status: completed  # in-work | completed | deferred
description: "Read-only UI to browse web_content searches and fetched pages. Adds a backend read-API (paginated list + detail GET endpoints) to the module and a Vue feature with two list→detail pages."
tags: [web_content, frontend, api]
---

## Task

Создать интерфейс просмотра запросов (`web_content_search`) и найденных страниц
(`web_content_page`) модуля `web_content`. Пример-ориентир по фронту — фича
`conversations` из соседнего проекта (`AGENTS/semaphore-core`).

Решения по объёму (подтверждены пользователем):
- **Две страницы**: Запросы (search → детальная с её результатами) и Страницы
  (page → детальная с контентом). Группа в сайдбаре «Web Content».
- **Read-only** — все эндпоинты GET, никаких write-действий.
- Контент страницы рендерится через `MarkdownRenderer`.

## Context

У модуля `web_content` не было HTTP-API вообще — `run_search` вызывался только
программно, а `fetch_pages` крутится фоновой задачей. Для просмотра данных нужен
read-API (по образцу `core_setup`: `internal_router` + `internal_router_prefix`)
и фронт-фича (по образцу локальных `features/settings|setup` + паттернов
`conversations`). Локально уже есть `PageLayout`/`PageHeader`/`TablePaginationBar`/
`internalApi`/`MarkdownRenderer`/`StatusBadge`/`ErrorState`; навигация — статический
массив в `AppSidebar.vue`, роуты — в `router/index.ts`, локали авто-мёрджатся из
`features/<name>/locales/ru.json` под неймспейсом = имя папки фичи.

## What was done

**Backend (read-API):**
- `crud/search.py` — `search_list` + `search_count` (фильтры query/status/provider, `sort_dir`, offset/limit).
- `crud/page.py` — `page_list` + `page_count` (фильтры query[url]/status/domain).
- `crud/search_result.py` — `results_with_page_for_search` (джойн result↔page для детальной запроса).
- `dto.py` (новый) — `Paged[T]`, `SearchRow`, `SearchResultView`, `SearchDetail`, `PageRow`, `PageDetail`.
  `SqlDateTime` (`PlainSerializer`) → даты в SQL-формате под фронт-парсер (Luxon `fromSQL`).
- `api.py` (новый) — GET `/searches`, `/searches/{id}`, `/pages`, `/pages/{code}`; `ApiError.not_found` на 404.
- `module.py` — `internal_router` + `internal_router_prefix="/web-content"`.

**Frontend (`web/src/features/web_content/`):**
- `api.ts` (DTO + 4 функции), `labels.ts` (статус→цвет StatusBadge), `routes.ts` (4 роута).
- stores: `searches`/`pages` (списки с фильтрами+пагинацией), `search-detail`/`page-detail`.
- views: `SearchesView`/`PagesView` (фильтр-VCard + VDataTable + TablePaginationBar),
  `SearchView` (запрос + выдача, клик по результату → страница), `PageView` (метаданные + `MarkdownRenderer`).
- `locales/ru.json` (неймспейс `web_content`, авто-мёрдж).
- Регистрация: роуты в `router/index.ts`, nav-группа «Web Content» (Запросы/Страницы) в `AppSidebar.vue`.

**Тесты:** `tests/modules/web_content/test_api.py` (новый, 6 тестов: списки/детальные/404/без-контента-в-списке) +
расширен `test_crud.py` (list/count/пагинация/фильтры/джойн). Было 26 → стало 37 тестов модуля.

## Problems

Несоответствие формата дат: фронт-парсер (`shared/utils/date.ts`) использует Luxon `fromSQL`
(SQL-формат с пробелом), а pydantic по умолчанию отдаёт ISO с `T` → даты рендерились бы как «—».
Решено локально в DTO: тип `SqlDateTime` с `PlainSerializer`, сериализующим в `"yyyy-MM-dd HH:mm:ss"`.

## Result

- Verified: `uv run pytest --core --module=web_content` → 296 passed; `vue-tsc --noEmit` → 0; `vite build` → ok.
- Создано: `src/modules/web_content/{api.py,dto.py}`, `tests/modules/web_content/test_api.py`,
  весь каталог `web/src/features/web_content/` (api/labels/routes + stores/ + views/ + locales/).
- Изменено: `crud/{search,page,search_result}.py`, `module.py`, `web/src/router/index.ts`,
  `web/src/layout/components/AppSidebar.vue`, `AGENTS/docs/web_content/INDEX.md`.
- `web/dist/` пересобран (build-артефакт; коммитится отдельно по протоколу).
- Read-only, как заказано. Открыто на будущее: write-триггер `run_search` из UI; рефетч страницы.

Status: **completed**.
