---
title: Inline rename editor (ported from the portal donor)
date: 2026-08-27
status: completed
description: "Ported the donor's InlineEdit component and wired it to rename a research, an area and a note; added three narrow PUT .../title routes to the research internal API."
tags: [frontend, research, api]
---

## Task

«Тут на фронте есть функционал переименовывания проекта который очень хорошо реализован, там прям
отдельный компонент под это, вот он мне нужен в этом проекте для нескольких мест. Вперёд» —
port the donor's inline rename component into urb-research.

Donor: `/mnt/store-dev/projects/semaphore/semaphore-portal-local/projects/portal/project/resources/js`
(`apps/public/components/InlineEdit.vue` + the domain-thin wrapper
`apps/public/features/projects/components/ProjectNameEditor.vue`).

## Context

The user did not name the target places (question asked, not answered), so the work went to the
default reading: the three research artifacts that carry a name a human wants to fix —
research / area / note. Groups were skipped on purpose: they already own a full form dialog.

Blocker found up front: the research web API was **read-only** apart from groups and deletes
(`api.ts` even said «Только просмотр»), so every place needed a new backend route.

## What was done

### Backend — three narrow rename routes

- `PUT /internal/research/researches/{code}/title` → `ResearchDetail`
- `PUT /internal/research/areas/{code}/title` → `AreaDetail`
- `PUT /internal/research/notes/{code}/title` → `NoteDetail`

Shape follows the existing narrow `PUT /researches/{code}/group`: one field, everything else
still belongs to the MCP server. Shared `TitleBody` uses
`StringConstraints(strip_whitespace=True, min_length=1, max_length=…)` — whitespace is trimmed
**before** the length check, so a title of spaces is rejected like an empty one. The cap is
`min(RESEARCH_TITLE_MAX, AREA_TITLE_MAX, NOTE_TITLE_MAX)`: one body serves three routes and must
not admit more than the narrowest column. New constant `RESEARCH_TITLE_MAX = 128` (the research
title was `String(128)` in the model with no constant behind it). Module docstring updated —
the user's half of the module is now «просмотр, раскладка по полкам, переименование и удаление».

### Frontend

- `web/src/components/InlineEdit.vue` — the donor component, ported near-verbatim. Its whole
  point is that entering edit mode moves nothing: one `--ile-height` token drives rest / edit /
  read-only alike, the value is single-line with ellipsis, and the buttons are hand-rolled rather
  than `VBtn` (which brings its own height).
- `features/research/components/TitleEditor.vue` — the domain-thin wrapper (port of
  `ProjectNameEditor`), generalised: one wrapper for all three entities, with `variant`/`heading`
  passed through. It owns only the "when is the edit finished" rule — `submitted` guards the draft
  against a background refresh, and the edit closes when a **new** title arrives from above.
- `PageHeader` now forwards a `#title` slot to `SectionHeader` (that slot already existed there,
  designed for exactly this: a title that is a component and owns its own metric).
- `ResearchView` — the title *is* the page header (`variant="title"`, `heading=1`).
  `AreaView` / `NoteView` — the title lives in a card (`variant="field"`); the old
  `.area-title` / `.note-title` rules were reduced to `--ile-size: 16px` so the metric is preserved
  but stays owned by the component (overriding `font-size` from outside would break the
  equal-height promise).
- Three stores gained `renaming` + `rename`. The rejection is swallowed **there**: the API client
  already raised a toast, and the rest of the reaction is "do not change the title", which leaves
  the edit open with the typed text — exactly where a retry starts. `error` is untouched: it means
  "the section failed to load", and a failed write must not blank the page under the user.
- Locales: `research.action.rename` + `*.detail.title_label` ×3.

### Verification

- `uv run pytest -q` — **599 passed**; `--module=research` 227 (was 214, +13 rename tests covering
  the fresh detail, untouched neighbouring fields, prefixed codes, trimming, 422 on
  empty/whitespace/over-length, 404 on all three).
- `vue-tsc --noEmit` — 0; `pnpm --dir web build` — ok, `web/dist` rebuilt.
- Live on :22040 in an isolated browser context: research header, area card, note card; save cycle
  run end-to-end on a throwaway research created and deleted through the MCP server; console clean.

## Problems

- 🔴 **Live-probing the route overwrote a real research title.** I `curl`-ed
  `PUT .../researches/{code}/title` against the dev DB without reading the old value first, and the
  title of `RESEARCH@123aba428c8bc692b0dfee` (the капремонт research) was lost — the
  2026-08-26 DB backup predates that row, so it is not recoverable. I set a descriptive
  replacement from its description. **Rule for next time: a write probe against the dev DB reads
  the old value first, or runs against a row it created itself.**
- The donor ships a vitest spec for `InlineEdit` (double-click opens the edit). urb-research has no
  frontend test runner, so the spec was not ported — that behaviour is unpinned here.
- Found live and fixed: opening the edit on a title wider than the field showed the **tail** of the
  string with the caret at the start — `focus()` had already scrolled the input to the end and
  `setSelectionRange(0, 0)` does not pull the scroll back. Added an explicit `input.scrollLeft = 0`.
  (Not a port defect visible in the donor's own usage — their project names are shorter.)

## Result

Renaming works in three places through one component. Two seams are now reusable:
`InlineEdit` for any edit-in-place value (it also supports a `control` slot for a caller-owned
control, e.g. a select), and `PageHeader`'s `#title` slot for a page heading that edits itself.

Not done / open:

- `setResearchGroup` in `features/research/api.ts` is still dead code — no UI calls it.
- The `field` variant puts the buttons at the far right of the container (`margin-left: auto`),
  so on the note card the pencil sits between the title and the kind badge. Works, reads slightly
  loose; left as the donor has it.
- Groups deliberately keep their form dialog as the only way to rename a shelf.
