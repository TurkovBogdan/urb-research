---
title: Balance & limits per connector (Tavily / Firecrawl / xAI)
date: 2026-07-06
status: in-work
description: "Определить, как узнать бюджет (остаток кредитов) и лимиты каждого коннектора core_connectors через API — живьём снять реальные shape'ы read-эндпойнтов. Затем добавить недостающие методы гейтвеям и спроектировать нормализованный интерфейс баланса/лимитов."
tags: [core_connectors, balance, limits, bench, tavily, firecrawl, xai]
---

## Task

«Посмотреть, как узнать бюджет текущих шлюзов. Нужны методы баланса и лимитов для каждого сервиса — определить их, потом подумать над интерфейсом.» Затем: «сохрани всё как задачу с подробным описанием».

## Context

Модуль `core_connectors` — тонкие коннекторы к внешним API (Tavily, Firecrawl, xAI). У гейтвеев уже были методы, близкие к «сколько осталось»: `TavilyGateway.usage()`, `FirecrawlGateway.usage()`, `XaiGateway.api_key_info()`/`models()`. Но реальные формы ответа (какие поля = остаток, какие = лимит/период) были сняты живьём не для всех — по докам/частично. Нужно определить это фактом, чтобы потом спроектировать единый интерфейс баланса/лимитов.

## What was done

Написан определяющий бенч `dev/bench/core_connectors/run_balances.py` — грузит store коннектора (реюз `xai.bootstrap.load_gateway_store`), дёргает read-only эндпойнты всех трёх сервисов, складывает сырьё в `dev/bench/core_connectors/tmp/balance_<service>.json`. Прогнан живьём (только GET, ничего не тратит) — ключи из dev-настроек. Реальные shape'ы:

### Tavily — `GET /usage` (`TavilyGateway.usage()`)
```
key:     { usage, limit(null), search_usage, crawl_usage, extract_usage, map_usage, research_usage }
account: { current_plan:"Researcher", plan_usage:17, plan_limit:1000,
           search_usage/crawl_usage/extract_usage/map_usage/research_usage,
           paygo_usage:0, paygo_limit:null }
```
- Остаток = `account.plan_limit − account.plan_usage` (983); плюс pay-as-you-go `paygo_limit − paygo_usage` (тут null/0).
- Лимит = `account.plan_limit` + `current_plan`; `key.limit` = per-key cap (тут null).
- Одна кредитная ось + разбивка по методам. **Дат периода нет.**

### Firecrawl — три эндпойнта
```
GET /v2/team/credit-usage → data{ remainingCredits:898, planCredits:1000, billingPeriodStart/End }
GET /v2/team/token-usage  → data{ remainingTokens:13470, planTokens:15000, billingPeriodStart/End }
GET /v2/team/queue-status → { maxConcurrency:2, jobsInQueue, activeJobsInQueue, waitingJobsInQueue, mostRecentSuccess }
```
- **Две независимые оси бюджета**: кредиты И токены, у каждой remaining/plan/период.
- Отдельный concurrency-лимит (`maxConcurrency`) + живая глубина очереди.
- На гейтвее заведён только `usage()` (= credit-usage). `token-usage` и `queue-status` дёргались через `_request` — **методов пока нет**.

### xAI — `GET /v1/api-key` + `GET /v1/models`
```
/v1/api-key → { redacted_api_key, name, team_id, acls[], api_key_blocked, api_key_disabled, team_blocked, ... }
/v1/models  → data[] с пер-модельными ценами: prompt_text_token_price, completion_text_token_price,
              cached_prompt_text_token_price, *_long_context, long_context_threshold, context_length
```
- **Остатка кредитов через inference-API (`api.x.ai`) НЕТ** (подтвердилось). Есть только права (`acls` = разрешённые модели/эндпойнты) и статусные флаги.
- Пер-модельные цены (в «ticks»); фактический расход — только пост-фактум в `usage.cost_in_usd_ticks` каждого ответа `responses()`.
- **НО баланс доступен через отдельный Management API** (сверено доками 2026-07-06):
  - База **`https://management-api.x.ai`** (не `api.x.ai`) + **отдельный Management Key** (Console → Settings → Management Keys, право *Management Keys Read*/billing; ≠ `xai_api_key`). Auth — `Authorization: Bearer <management_key>`.
  - `team_id` берём из inference `api_key_info().team_id` (`a838c37e-…`).
  - Остаток: `GET /v1/billing/teams/{team_id}/prepaid/balance` → `total` (USD-центы) + `changes[]`.
  - Лимиты: `GET /v1/billing/teams/{team_id}/postpaid/spending-limits` → `effectiveHardSl`/`softSl`/`effectiveSl`.
  - Ещё: `GET …/postpaid/invoice/preview` (превью счёта), `POST …/usage` (историческое потребление).
  - **Живьём НЕ проверено** — management-ключа в dev-настройках ещё нет (blocker). Детали → `AGENTS/research/xai/INDEX.md` (раздел «Billing / баланс»).

### Сводка
| Сервис | Остаток | Лимит плана | Доп. оси | Rate/concurrency | Период |
|---|---|---|---|---|---|
| Tavily | plan_limit−plan_usage (+paygo) | plan_limit + current_plan | usage по методам | — | — |
| Firecrawl | remainingCredits **и** remainingTokens | planCredits / planTokens | 2 оси бюджета | maxConcurrency + очередь | billingPeriodStart/End |
| xAI | ❌ нет | acls (разрешённые модели) | cost_in_usd_ticks/ответ; цены /v1/models | ❌ | — |

## Open / next steps

1. **Дозавести методы FirecrawlGateway:** `token_usage()` (`GET /v2/team/token-usage`) и `queue_status()` (`GET /v2/team/queue-status`) — сейчас доступны только через приватный `_request`.
2. ✅ **xAI balance через Management API — СВЕРЕНО ЖИВЬЁМ 2026-07-06** (management-ключ добавлен пользователем). `XaiManagementGateway.prepaid_balance(team_id)` → `total.val` + `changes[]`; `spending_limits` → нули (prepaid-only). ⚠ **знак инвертирован:** PURCHASE отрицательные, SPEND положительные, `FAILED_TO_CHARGE` не в сумме → **остаток = −`total.val`** (пример: `total.val="-602"` = $6.02 на балансе). Детали/гоча → `research/xai/INDEX.md`. Blocker снят.
3. **Интерфейс баланса/лимитов (обсудить).** Единый скаляр не ложится: Tavily — одна кредитная ось; Firecrawl — ≥2 оси (credits+tokens) + concurrency; xAI — остаток только через **отдельный Management API** (второй ключ, USD-центы). Кандидат — нормализованный «список бюджетов»: `[{axis, remaining, limit, unit, period_end?}]` + опц. `concurrency`/`plan`; сервис заполняет что может. Форму согласовать с пользователем перед реализацией.
4. Возможно — предусмотреть общий базовый гейтвей (см. задачу-ревью рефакторинга) как дом для будущего `balance()`/`limits()`.

## Result

- Новый бенч `dev/bench/core_connectors/run_balances.py` (+ артефакты `tmp/balance_{tavily,firecrawl,xai}.json`), прогнан живьём — реальные shape'ы баланса/лимитов зафиксированы для всех трёх сервисов.
- Определение завершено; добавление методов и интерфейс — следующими шагами (в работе).
