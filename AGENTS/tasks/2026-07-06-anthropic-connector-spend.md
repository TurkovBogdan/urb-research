---
title: Anthropic (Claude) connector (spend-only, Admin Cost Report) in core_connectors
date: 2026-07-06
status: completed
description: "Добавить Anthropic (Claude) как коннектор — метрика «Расход за 30 дней» через Admin Cost Report (остатка баланса нет). Auth иная (x-api-key + anthropic-version). Живая сверка — по получении Admin-токена."
tags: [core_connectors, anthropic, claude, spend, balance]
---

## Task

«Теперь аналогично anthropic + инструкция по получению ключа.» По образцу OpenAI-коннектора (`2026-07-06-openai-connector-spend`). Research: `AGENTS/research/anthropic/INDEX.md`.

## What was done

- **`services/anthropic/gateway.py::AnthropicGateway(ServiceGateway)`** — только расход. `api.anthropic.com/v1`, **Admin-ключ** `anthropic_admin_api_key` (`sk-ant-admin…`), тумблер `anthropic_gateway_enabled`, `HAS_BALANCE=True`, `SPEND_WINDOW_DAYS=30`.
  - ⚠ **Auth иная** — не `Bearer`, а `x-api-key` + `anthropic-version: 2023-06-01` (переопределён `_auth_headers`).
  - `cost_report(starting_at, …)` → `GET /organizations/cost_report` (bucket 1d). `_fetch_balance`: `starting_at = now−30д` (RFC3339, `utc_now()`).
  - `_parse_balance`: ⚠ `amount` — строка в **ЦЕНТАХ** → **`Σ float(amount) / 100`** = доллары → метрика `BalanceMetric.money("Расход 30д", …)`.
- **База:** авторизация вынесена в переопределяемый **`_auth_headers()`** (default Bearer) — ради Anthropic-схемы; обратно совместимо (прочие коннекторы не тронуты).
- **Настройки:** `anthropic_gateway_enabled` + `anthropic_admin_api_key` (secret). **Реестр:** зарегистрирован (6 коннекторов).
- **Тесты** (+2 → 14): центы-строка → $2.00; `_auth_headers` = `x-api-key`+`anthropic-version`, без `Authorization`.

## Result

- Фронт/dist НЕ менялись (data-driven: Claude — 6-я карточка). Реестр: `[…, 'openai', 'anthropic']`.
- `--module=core_connectors` 14 / полный дефолт **343 passed**. Docs + MEMORY + research обновлены.

**Параллельность балансов (проверка по запросу):** `ConnectorsRegistry.connectors()` уже собирает балансы всех сервисов через `asyncio.gather` (каждый `balance()` — async httpx со своим клиентом → сетевые запросы одновременно, не по очереди). Закреплено **детерминантным тестом** `test_connectors_balance_fetched_in_parallel` (считает пик одновременно активных `balance()` = 4, а не 1; без таймингов). Модуль **15 passed**.
- ⚠ **Живая сверка — pending:** нужен **Admin-ключ** `sk-ant-admin…` от пользователя (обычный `sk-ant-api…` → нет доступа к cost_report). После получения — прогнать через коннектор / задать в Настройки → Сервисы. Может всплыть нюанс auth (x-api-key vs Bearer) — проверю по факту.
