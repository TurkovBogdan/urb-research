---
title: Researches list — shelf and delete verbs in the row menu
date: 2026-08-27
status: completed
description: "Added file / move / detach shelf and delete-research to the researches-list kebab, in the group dialogs' idiom; +7 API tests for the shelf paths the menu walks."
tags: [frontend, research, tests]
---

## Task

«Смотрим реализацию модалок в группах и добавляем к списку исследований в меню с тремя точками
кнопки привязать группу, сменить группу, удалить исследование. Всё покрываем тестами. А и
отвязать группу.»

## Context

The group dialogs (`GroupFormDialog` / `GroupDeleteDialog`) set the house idiom, and it was
followed verbatim:

- the shell is `AppDialog`; the destructive one is `ConfirmDialog`, which **asks** while the caller
  **acts** — that split is what keeps the dialog open on failure;
- the form keeps its own copy of the values and syncs on open, so cancelling leaves the list intact;
- writes go with `report: false` so the refusal renders next to the button instead of as a toast
  that walks away from where the user is looking;
- `busy` locks the buttons and makes the dialog `persistent`.

Both backend routes already existed and were unused from the UI: `PUT /researches/{code}/group`
(`setResearchGroup` was dead code in `api.ts`) and `DELETE /researches/{code}` — the open thread
from `2026-08-27-research-user-delete-routes.md`, now closed for the research level.

## What was done

### Menu (`ResearchesTable.vue`)

```
Открыть карточку
Открыть полку              (disabled when ungrouped)
──
Положить на полку          (ungrouped) │ Переложить на другую полку  (grouped)
Снять с полки              (grouped only)
──
Удалить исследование       (danger-coloured, label + icon)
```

Filing and moving share one dialog: the field is the same and only the title differs; a second
component would mean two forms drifting apart at the first new field. Detaching gets **no** dialog —
there is nothing to choose and it is reversible; it has its own in-flight guard (`detaching`) so a
second click cannot fire a second request, and its refusal is left to the toast because a menu item
has no place of its own to show a message.

### Dialogs

- `ResearchGroupDialog.vue` — a shelf select. Loads the groups itself when the store is empty (the
  registry page had already loaded them, the shelf page had not). Save is blocked while the choice
  equals the current shelf: there is nothing to save.
- `ResearchDeleteDialog.vue` — `ConfirmDialog` plus a list of what the cascade takes (areas /
  searches / sources, built from the counters already in the row, zero-count lines dropped) and an
  irreversibility line in the error colour.

Both dialogs live in the table, next to the menu that opens them, and report back through
`afterChange()` — which reloads the list **and** the groups, since a shelf carries a research
counter that goes stale with the same write.

### Tests (+7, all `--module=research`)

The existing suite covered ungrouped→shelf and shelf→none; the paths the new menu walks did not
exist yet:

- moving between two shelves, and the two shelf counters shifting with it;
- detaching keeps both the research and the shelf; detaching an already-ungrouped research is a
  200 no-op (the menu hides the item, but a repeat must not be an error);
- a detached research shows up under the "ungrouped" filter;
- a bare (unprefixed) group code resolves like a prefixed one;
- a move to a missing group is 404 **and leaves the current shelf in place**.

`uv run pytest -q` — **612 passed** (was 599). `vue-tsc` 0; `web/dist` rebuilt.

### Live check (:22040, isolated browser context)

Walked the whole cycle on a throwaway research and two throwaway shelves created through the MCP
server: menu shape on an ungrouped row (no detach item, «Открыть полку» dimmed) → file on shelf A
(save stays disabled until a shelf is picked) → menu shape on a grouped row (move + detach appear)
→ move dialog opens with the current shelf preselected and save **disabled until the choice
changes** → move to shelf B (verified in the DB) → detach (verified in the DB) → delete dialog
listing «зон: 1» → deleted, row gone from the list. Console clean; all temporary rows removed
afterwards and verified gone.

## Problems

- No frontend test runner in this project, so «всё покрываем тестами» is covered at the API level
  only; the dialog behaviour (preselect, disabled-until-changed, open-on-failure) is pinned by the
  live walk-through above, not by a test.

## Wording pass (same day)

The user rejected the shelf metaphor: «У нас не полки а группы». The entity is called *группа*
everywhere in the app (nav, the `/research/groups` section, its own dialogs) — the shelf wording
was mine, and it had also leaked into two pre-existing strings.

Retranslated to the user's own verbs (привязать / сменить / отвязать):

| key | было | стало |
|-----|------|-------|
| `action.open_group` | Открыть полку | Открыть группу |
| `action.set_group` | Положить на полку | Привязать группу |
| `action.move_group` | Переложить на другую полку | Сменить группу |
| `action.unset_group` | Снять с полки | Отвязать группу |
| `group.file_title` | Положить на полку | Привязка группы |
| `group.move_title` | Переложить на другую полку | Смена группы |
| `group.field` | Полка | Группа |
| `group.no_groups` | Полок пока нет… | Групп пока нет… |
| `group.list.description` | Полки реестра: исследование лежит максимум на одной. | Группы реестра: исследование входит максимум в одну. |
| `group.ungrouped.description` | …ещё не разложены по полкам. | …ещё не привязанные ни к одной группе. |

Dialog titles are nominal («Привязка группы» / «Смена группы») to match the section's existing
«Изменение группы» / «Удаление группы» / «Новая группа».

Russian comments in the files written this session were retranslated with them, so the code stops
contradicting the screen. Verified live: menu on an unattached research shows «Привязать группу»
and no detach item; after attaching, «Сменить группу» + «Отвязать группу»; both dialog titles
correct; the `/research/groups` page carries the reworded descriptions. `vue-tsc` 0, 612 passed,
`web/dist` rebuilt, temporary rows removed.

⚠ **Not swept**: the shelf metaphor still sits in ~190 Russian comments/docstrings across the rest
of the module (`src/modules/research/**`, incl. applied migrations, `crud`, `dto`, the MCP layer,
tests, and the older frontend files) and as the English word *shelf* in the agent-facing MCP
instructions (`mcp/__init__.py`: «a shelf researches are filed under»). That is internal
vocabulary, not translation, and a rename of that size deserves its own pass.

## Result

The research level of the list is now fully operable from the row menu: open, shelve, reshelve,
unshelve, rename (previous task), delete.

Not done:

- Deleting an area / search / note from their own pages — the routes exist, the UI does not.
- The kebab has no «переименовать»: renaming lives on the detail page, in place.
