---
title: OpenAI connector (spend-only, Admin Costs API) in core_connectors
date: 2026-07-06
status: completed
description: "Добавить OpenAI как коннектор — метрика «Расход за 30 дней» через Admin Costs API (остатка баланса у OpenAI нет). Нужен Admin-ключ. Живая сверка — по получении токена от пользователя."
tags: [core_connectors, openai, spend, balance]
---

## Task

«Заводи под openai, токен дам.» Предыстория (research): у OpenAI **нет** API остатка баланса (`credit_grants` — только браузерный session-токен); программно доступен лишь **расход** через Admin Costs API (`AGENTS/research/openai/INDEX.md`).

## What was done

- **`services/openai/gateway.py::OpenAIGateway(ServiceGateway)`** — только расход. `api.openai.com/v1`, `TIMEOUT=30`, **Admin-ключ** `openai_admin_api_key` (обычный `sk-…` → 403), тумблер `openai_gateway_enabled`, `HAS_BALANCE=True`, `SPEND_WINDOW_DAYS=30`.
  - `costs(start_time, …)` → `GET /organization/costs` (bucket_width=1d).
  - `_fetch_balance`: `start_time = now − 30д` (`time.time()`), limit=31.
  - `_parse_balance`: **Σ `data[].results[].amount.value`** (доллары) → метрика `BalanceMetric.money("Расход 30д", …)`. Пустой ответ → $0 (метрика есть).
- **База:** `_request` получил параметр `params` (query) — costs требует `start_time`/`bucket_width`; обратно совместимо (default None).
- **Настройки:** `openai_gateway_enabled` (Bool) + `openai_admin_api_key` (secret) — runtime (ENV отложено, как у прочих).
- **Реестр:** зарегистрирован `OpenAIGateway()` (теперь 5 коннекторов).
- **Тесты** (+2 → 12): сумма бакетов → «Расход 30д» $0.20; пустой → $0.

## Result

- Фронт/dist НЕ менялись (data-driven: OpenAI — 5-я карточка, поля ключа в Настройки → Сервисы).
- Реестр: `['tavily','firecrawl','xai','openrouter','openai']`. `--module=core_connectors` 12 / полный дефолт **341 passed**. Docs + MEMORY + research (openai/anthropic) обновлены.
- ✅ **Сверено ЖИВЬЁМ** (Admin-ключ `sk-admin-…` добавлен пользователем): endpoint отдал «Расход 30д» = **$3.51**. Всплыло два факта: (1) проектный ключ `sk-proj-…` → **403** (нужен именно admin); (2) реальный `amount.value` — **строка** высокой точности (`"2.714…"`), не float как в доках → пофикшен `float(value)` в `_parse_balance` (+тест на строковые значения). Детали → research/openai.
- **Не сделано (по решению/следующим шагом):** Anthropic (Claude) — аналогичный расход, но `amount` в **центах-строке** (`Σ/100`), Admin-ключ через `x-api-key`+`anthropic-version`.
