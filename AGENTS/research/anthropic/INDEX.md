---
title: Anthropic (Claude) — баланс/расход через API
date: 2026-07-06
description: "У Anthropic НЕТ API остатка баланса (только console). Программно доступен лишь РАСХОД через Admin API (Cost Report / Usage Report). Эндпойнты, auth, схемы. По офиц. докам."
tags: [external-service, billing]
---

## Scope

Можно ли получить баланс/расход Claude программно (для коннектора-мониторинга). По офиц.
докам platform.claude.com; живьём НЕ гоняли (нет Admin-ключа).

## Findings

- **Остатка баланса через API НЕТ.** `GET /v1/organizations/balance` → 404. Остаток — только в
  console.anthropic.com (Billing). Есть открытый feature request (не реализован на 2026).
- **Есть РАСХОД — Admin API** (нужен **Admin API-ключ**, отдельный от обычного `sk-ant-…`;
  создаётся Console → Admin keys; header `anthropic-version: 2023-06-01`):
  - **Cost Report** — `GET https://api.anthropic.com/v1/organizations/cost_report`
    - Params: `starting_at` (RFC3339, обяз.), `ending_at` (опц.), `bucket_width="1d"`,
      `group_by[]` (`description`/`workspace_id`), `limit`, `page` (next_page-курсор).
    - Ответ: `{data: [{starting_at, ending_at, results: [{amount, currency, cost_type,
      model, service_tier, token_type, context_window, workspace_id, description}]}],
      has_more, next_page}`.
    - ⚠ **`amount` — строка в ЦЕНТАХ** (lowest currency units, десятичная): `"123.45"` USD = **$1.23**.
      `currency` всегда `"USD"`. **Итоговый расход = Σ float(results[].amount) / 100** (по всем
      бакетам + пагинация по `next_page`).
    - ⚠ Priority Tier costs в cost_report **не** входят — их только через usage_report.
  - **Usage Report** (токены, не деньги) — `GET /v1/organizations/usage_report/messages`
    (bucket 1m/1h/1d, разбивка по модели/воркспейсу/tier).
- Данные появляются ~5 мин после запроса; поллинг раз в минуту.

## Limits / quirks

- Нет остатка → для коннектора максимум «Расход за N дней» (метрика-деньги без total), не баланс.
- Admin-ключ обязателен (обычный `sk-ant-…` к cost_report доступа не даёт).
- На Claude Platform на AWS Usage/Cost API недоступны; Enterprise — отдельный Analytics API.

## References

- Usage & Cost API guide: https://platform.claude.com/docs/en/manage-claude/usage-cost-api
- Cost Report ref: https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report
- Feature request (balance): github.com/anthropics/claude-code/issues/47574
