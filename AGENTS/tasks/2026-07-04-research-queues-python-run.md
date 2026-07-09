---
title: Run research «Создание системы очередей на Python» into research_registry
date: 2026-07-04
status: completed  # in-work | completed | deferred
description: "First real research recorded into research_registry: topic «creating a queue system in Python». Acted as the orchestrator (services/ not yet automated) — live search/research via urb-research MCP, wrote research → queries → documents → reports into the dev DB via module CRUD. Populates the new viewer."
tags: [research_registry, research, demo]
---

## Task

«Запусти исследования на тему создания системы очередей на python.»

## What was done

Слоя `services/` (авто-оркестрация) ещё нет → оркестратором выступил агент:
- Тема разбита на 3 подзапроса: Celery+Redis · встроенные `queue`/`asyncio.Queue`
  (producer-consumer, backpressure) · сравнение Celery/RQ/Dramatiq + брокеры
  (RabbitMQ/Redis/Kafka).
- По каждому — живой `mcp__urb-research__search` (источники: title/url/snippet) +
  `mcp__urb-research__research` (полный markdown-отчёт, language=russian, depth=quick).
- Записано в research_registry (dev-sqlite) через CRUD модуля seed-скриптом
  `dev/bench/research_registry/seed_queues_research.py` (только INSERT + create_all
  checkfirst, без деструктива): 1 research (status `done`) → 3 queries (`reported`) →
  15 documents (url/title + саммери + relevance 0.55–0.95) → 3 reports.

## Result

- dev-БД: research id=1 «Создание системы очередей на Python», 3 queries, 15 docs,
  3 reports — подтверждено `dev-query.sh`.
- Видно во вьюере: сайдбар → Данные → Исследования (`/research/researches`).
- Seed-скрипт переиспользуем (idempotent на схему, но каждый запуск создаёт новое
  research — не дедуплицирует).

Примечание: это ручная оркестрация. Автоматизация (тул `research()` в MCP, который
сам гоняет web_content + синтез) — задача слоя `services/` в `research_registry`.
