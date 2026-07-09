---
title: Pre-public-commit secret & internal-info audit
date: 2026-07-09
status: completed
description: "Audit the repo before its first public commit: verify .gitignore, hunt for credentials/access tokens and internal info that would leak, and scrub what was found."
tags: [security, git, cleanup]
---

## Task

Готовим первый коммит проекта в публичный репозиторий. Проверить `.gitignore` и всё
дерево на утечки доступов (креды/токены) и внутренней информации; вычистить найденное.
Решения пользователя: AGENTS/ оставляем, но чистим; утёкшие ключи убрать из файла.

## What was done

**Контекст:** репозиторий без коммитов (0 tracked) — это первый коммит, чистка до
истории (без rewrite).

- **`.gitignore` проверен — корректен:** реальный `.env` (внутри `DB_PASSWORD`, `MCP_TOKEN`),
  `runtime/*` (БД `app.sqlite3`, логи), `storage/*`, `secrets/`, `.claude/`, `.idea/`,
  `.coverage`, `dev/bench/**` артефакты — всё игнорируется.
- **🔴 Удалены реальные API-ключи** из `AGENTS/tasks/2026-07-02-web-search-provider-in-core-setup.md`
  (Tavily `tvly-dev-…`, Firecrawl `fc-…`) → заменены на отсылку к менеджеру секретов.
  Ключи считать скомпрометированными — пользователь отзывает/ротирует на стороне сервисов.
- **Симлинки в приватные сторы** `AGENTS/obsidian` (→ second-brain) и `AGENTS/semaphore-core`
  (→ другой проект) добавлены в `.gitignore` (на диске не тронуты, локальный воркфлоу цел).
- **Реальные email клиентов** (домены реальных компаний) в демо design-system
  (`MembersCellView.vue`, `MessageContentView.vue`) + email команды → заменены на `acme.example`.
- **Внутренние абсолютные пути** (store-mount пути + домашние пути с username) и
  прод-хостнейм → генерик-плейсхолдеры в `README.md`, `AGENTS/README.md`,
  `AGENTS/docs/platform/mcp-stdio-shim.md`, `AGENTS/docs/core_connectors/INDEX.md`,
  и 6 task-заметках (05-31, 06-02, 06-03, 06-13, 07-01, 07-08).
- **`web/dist` пересобран** (`pnpm build`) — собранный SPA коммитится, старые email были
  в минифицированных JS; после ребилда чист.

**Второй проход (исчерпывающий по AGENTS/ + все задачи):**
- **🔴 Реальные логин-креды** (личная почта + личный пароль разработчика) в 4 местах →
  отсылка на менеджер секретов: `AGENTS/tasks/2026-06-11-ds-table-vtable.md`,
  `AGENTS/tasks/INDEX.md`, `AGENTS/memory/dev_browser_login.md`, `AGENTS/memory/MEMORY.md`.
- **🔴 Реальный пароль тест-БД** (`TEST_DB_PASSWORD` из старого env) в
  `AGENTS/tasks/2026-06-29-tests-inmemory-db.md` → `CHANGE_ME`.
- Прочее чисто: нет vendor-ключей, hash'ей паролей, webhook/bot-токенов, JWT, приватных
  ключей, DSN с паролем, значений реального `.env`. `service@paypal.com` в i18n-доке —
  публичный пример экранирования `@`, оставлен. `AGENTS/tools/__pycache__/*.pyc` игнорируется.

**Третий проход (по запросу — перепроверка всего дерева + разбор `dev/`):**
- Аудит-записи (эта задача + `tasks/INDEX.md`) сами цитировали удалённые секреты дословно
  (email/пароли/хостнейм) — **редактированы**, значений в записях больше нет.
- `dev/bench/**/tmp/*.json` и `__pycache__` — игнорируются (сырые ответы Firecrawl/Tavily/xAI
  с внешним контентом не коммитятся). Трекаемые бенч-`.py` берут ключи из env/настроек —
  захардкоженных ключей нет.
- **Username-путь `/home/<user>/…` вычищен** из `dev/.run/*.xml` (5 файлов: pnpm-путь →
  портируемый `pnpm`), `dev/bench/web_search/firecrawl/compare_scrape.py` (путь к транскрипту
  → плейсхолдер), `AGENTS/docs/platform/overview.md`.

## Problems

- В коде секретов нет; значения из реального `.env` нигде в трекаемом дереве не всплывают.
- `web_scrapper` коннектор ссылается на `http://127.0.0.1:19020` (localhost-демон) — не
  утечка инфраструктуры, оставлено как есть.

## Result

Финальный скан чист: нет утёкших ключей, значений `.env`, прод-хостнейма, клиентских email
(ни в исходниках, ни в `web/dist`). Симлинки и `.env` игнорируются.

**Осталось на стороне пользователя:** отозвать/ротировать утёкшие Tavily и Firecrawl
ключи; сменить засвеченный личный пароль (особенно если переиспользуется где-то ещё).
