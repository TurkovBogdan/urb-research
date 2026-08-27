---
title: Drop the group's looks and position from the MCP surface
date: 2026-08-27
status: completed
description: "Remove the group icon and the sort position from the research MCP server — arguments, response fields and the group_icons tool. The agent must not see either field; the columns, the web API and the frontend pickers stay."
tags: [research, mcp, groups]
---

## Task

> «Убрать из MCP части информацию про иконки, чтобы агент вообще не видел поле иконки. Это лишняя
> информация.» — и следом: «убрать всё, что относится к сортировке групп, внутри MCP тоже не нужно».

## Context

`research_group` carries `icon` (a name from the curated palette in `research/icons.py`) and `sort`
(the position a human drags the shelf to). The MCP surface exposed both: as arguments on
`group_create` / `group_update`, as fields on every group DTO the agent reads, plus a dedicated
`group_icons` tool serving the 120-name palette. None of it is research work — it is how the shelf
looks and where it sits, decided by a person in the UI — so it only spent the agent's context and
invited it to fiddle with decoration instead of filing.

The columns, `crud/group.py`, the web API (`GroupBody` / `GroupRow` / `GroupListRow`) and
`icons.py` stay: the frontend pickers are the consumers that have business here.

## What was done

- `dto.py`: new MCP-facing `GroupScan` — code / title / description / updated_at, nothing else.
  The web-facing `GroupRow` keeps `icon` + `sort` and stays the base of `GroupListRow`.
- `mcp/group.py`: `icon` and `sort` dropped from `group_create` / `group_update`, `group_icons`
  tool removed, all group tools return `GroupScan`; module docstring rewritten. `group_list` still
  returns the user's display order — the agent sees the order without being able to set it.
- `mcp/__init__.py`: the group paragraph of `_INSTRUCTIONS` no longer mentions icons, the palette
  or `sort`; it says instead that the shelf's looks and place are the user's to set.
- Tests, listed in Result.

## Problems

The live smoke wanted a write (`group_create` through a fastmcp client), and a standalone
`uv run python` script resolves `Config()` to the **dev** DB — the rule in
`standalone_script_hits_dev_db` forbids exactly that kind of ad-hoc write. Verification was done
read-only instead (tool list + input/output schemas + server instructions), with every write path
covered by the in-memory suite.

## Result

Changed:

- `src/modules/research/dto.py` — `GroupScan` added (MCP), `GroupRow` kept as the web-facing DTO.
- `src/modules/research/mcp/group.py` — `icon`/`sort` gone from `group_create` / `group_update`,
  `group_icons` tool deleted, `GroupScan` returned everywhere, `icons.py` import dropped.
- `src/modules/research/mcp/__init__.py` — group paragraph of `_INSTRUCTIONS` rewritten.
- `tests/modules/research/test_group_mcp.py` — icon/sort assertions dropped;
  `test_icons_returns_the_palette` deleted; `group_icons` asserted **absent** from the tool list;
  `test_list_is_in_display_order` now sets `sort` through CRUD (a human's act) and checks the agent
  still receives that order; new `test_the_agent_never_sees_how_the_shelf_looks_or_where_it_sits`
  (neither field in any `group_*` input schema, nor in `group_get` / `group_update` / `group_list`).
- `tests/modules/research/test_group_flow.py` — the two palette tests replaced by
  `test_the_users_icon_and_position_survive_an_mcp_update` (a human sets icon + sort through CRUD,
  an MCP `group_update` must not blank them); `test_reordering_shelves_…` reordered through CRUD;
  `test_sort_zero_is_not_swallowed` relocated to the web API, where `sort` still lives.
- `tests/modules/research/test_api.py` — `test_update_group_sort_zero_is_not_swallowed` (0 is a
  valid position, not an omitted field).
- `AGENTS/agent-primary.md` — tool count 23 → 30 (measured: already stale before this change,
  groups had added six).

Untouched on purpose: the `icon` / `sort` columns, `crud/group.py`, the web API
(`GroupBody` / `GroupRow` / `GroupListRow`), `icons.py` and `test_group_icons.py`.

Checks:

- `uv run pytest --all -q` → **618 passed, 3 skipped** (heavy self-skips without `TEST_PG_DSN`).
- Tool count **30** (was 31). Group input schemas: `group_create` → title/description,
  `group_update` → group_code/title/description, `group_get`/`group_delete` → group_code,
  `group_list` → none. Output schemas of `group_get`/`group_update` → code/title/description/
  updated_at. Server instructions contain neither `icon`, nor `sort`, nor `palette`.

⚠ A running backend keeps the old MCP surface until it is restarted — the stdio shims of both
checkouts serve tools from the live process.
