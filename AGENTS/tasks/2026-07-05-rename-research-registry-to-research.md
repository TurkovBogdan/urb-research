# Rename module research_registry → research

**Status:** completed
**Opened:** 2026-07-05
**Closed:** 2026-07-05

## Goal
Полное переименование доменного модуля до финального имени `research` (консистентно: бэкенд, фронтенд, миграции, MCP-код, память). Шло в два прохода за одну сессию: `research_registry` → `research_database` → `research` (пользователь упростил имя по ходу).

## Decisions (confirmed with user)
- Финальное имя модуля — `research` (совпадает с route-префиксом `/research` и с сущностью — i18n-ключи стали `research.research.*`, двойной, но рабочий; плоскую перестройку локали НЕ делали).
- Migration revision-id prefix — `rem_` (research + m). Итог: `rem_001..004`.
- MCP mount-код — `research` (`/mcp/research`). Внешний клиентский алиас `urb-research` — отдельное имя, не затрагивается.

## Done (финальное состояние = `research`)
- Backend: dir `src/modules/research`; все import-пути `src.modules.research`; класс `ResearchModule`; `name="research"`; mcp-код `research`; docstrings. `build_modules()` импортируется чисто (class `ResearchModule`, mcp `['research']`).
- Migrations: файлы `rem_001..004` + revision-id + down_revision-цепочка (001→None, 002→rem_001, 003→rem_002, 004→rem_003). `migrate check` rc=0.
- Frontend: dir `web/src/features/research`; i18n namespace = имя папки → `t('research.*')` (сущностные ключи `research.research.*`); pinia store-id `research-*`; export `researchRoutes` + import/spread в `router/index.ts`; `AppSidebar` labelKey. `vue-tsc --noEmit` rc=0.
- Bench dir `dev/bench/research` + импорты + комменты. MEMORY.md — 2 упоминания в web_search-записи (`research \`rem_*\``, «дедуп: research тоже»).
- Прозаические «реестр»/«registry» описания намеренно оставлены (описывают функцию, не идентификатор).
- Домены НЕ тронуты: таблицы `research`/`research_query`/`research_document`/`research_report`, классы `Research`/`ResearchQuery`/`ResearchDocument`/`ResearchReport`, URL `/research`.
- Проверки: core-тесты 266 passed; глобальный grep по коду — ноль остатков `research_registry`/`research_database`/`rrm_`/`rdm_`.

## dev-БД (отклонение от «полной пересборки»)
Имена таблиц не менялись (только revision-id) → схема побайтово идентична; research-таблицы пусты, `core_modules_settings` = 11 строк настроек. Вместо drop+rebuild — **точечный UPDATE указателя головы** `alembic_version`: `rrm_004` → `rdm_004` → `rem_004`. `migrate check` rc=0, настройки/данные сохранены.

## Follow-up (пользователю)
- **Перезапустить backend** — запущенный процесс держит в памяти старый модуль (папки уже нет), hot-reload на нём упадёт: `bash AGENTS/tools/restart-backend.sh`.
- Обновить URL MCP-клиента → `/mcp/research` (клиентский алиас `urb-research` не меняется).
