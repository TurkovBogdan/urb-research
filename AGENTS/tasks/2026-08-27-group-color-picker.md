---
title: Group colour picker (frontend reference + design-system component)
date: 2026-08-27
status: in-work
description: "A colour for a research group: a fixed named palette on the frontend plus a picker component in the design system. Stage one is frontend only — backend column and MCP surface come later."
tags: [frontend, design-system, research]
---

## Task

«В дизайн систему нужно добавить качественный компонент выбора цвета. Это не произвольный цвет, а
выбор из предустановленного градиентного набора. Будет использоваться совместно с
RESEARCH@69a6859a09e878772e28b6 — его мы добавим в модалку `/research/groups`. Сначала прорабатываем
компонент, потом бек и MCP. Цвета у нас в текстовом формате по именам, но не исключено, что потом
пойдёт кастом. Сейчас нужен справочник цветов на фронте и компонент выбора в дизайн-системе.»

## Context

Research groups already carry an icon: the name is stored as text, the backend keeps the allowed
names in `research/icons.py::GROUP_ICONS` (served by the `group_icons` MCP tool), and the frontend
half is `features/research/constants/groupIcons.ts` + the shared `components/IconPicker.vue`, shown
in the design system at `/design-system/icon-picker` and used in `GroupFormDialog.vue`. Colour is
the same shape of problem, so it follows the same split: a named registry on the frontend, a shared
picker component, a design-system page — backend column and MCP surface in a later stage.

Two answers from the user shaped the palette:

- The set is **flat** (~16 named colours, no lightness ramp), and each swatch is painted with a
  two-stop gradient of its own hue.
- The colour lands on the **group's icon plate** (the `--accent-soft` square with an `--accent`
  glyph on the group card), so each name has to yield a fill + a glyph tone that pass AA in both
  themes.

Open: the research code in the request (`RESEARCH@69a6859a09e878772e28b6`) is the Eiffel-tower
diagnostic run, not a colour study — flagged to the user, does not block this stage.

## What was done

**Palette (10 named colours, flat).** Generated with the OKLCH→hex utility from
`docs/frontend/rules.md`, not hand-picked: nine hues 40° apart around the wheel plus a neutral,
each frozen at three lightness steps (L 0.80 `light` / 0.62 `mid` / 0.47 `deep`), chroma asked for
0.20 and fitted down to the sRGB gamut per hue and level. Lightness is what stays equal across the
set — swatches read as one family — and chroma is whatever the hue can still hold there. A swatch
is the `mid` step, flat: one tone stands for the colour in either scheme. Both readable steps were
measured against the plate they actually land on (surface + a 14% tint of the step itself): worst
pair in the set 5.16:1, above the 4.5 AA asks for. The check mark on a swatch is a graphical
object, worst pairing 3.92:1 against `mid`, above the 3:1 that asks for.

The set was cut twice on the user's word — 16 gradient swatches → 12 flat → 10. Each time the hues
were **re-spaced**, not dropped: taking four out of sixteen would have left neighbours
(amber/yellow, emerald/teal, sky/cyan) that a person has to tell apart by shade. A swatch of the
middle step sits only ~2.8:1 off the tray in the light theme, so a tile carries a hairline inset
edge; without it the set read as one blur.

**Three files, three jobs.**

- `shared/colorTones.ts` — the contract: `ColorSteps` (three hex steps), `ColorToneVars`,
  `colorToneVars(steps)`. `null` steps yield the app accent, so an unset colour paints exactly as
  the interface did before colours existed.
- `features/research/constants/groupColors.ts` — the data: the ten names and their steps,
  `groupColor` / `groupColorNames` / `groupColorVars`. Mirrors `groupIcons.ts`, down to the
  fallback rule (an unknown stored name is not an error).
- `styles/main.scss` — the theme decision, once: `.color-tones` composes `--gc-ink` / `--gc-fill`
  / `--gc-swatch` out of the steps, and `:root[data-theme='light'] .color-tones` swaps the ink to
  `deep`. Consumers name roles, never steps.

**Component** `components/ColorPicker.vue` — a sunken tray of flat tiles, the same shell as
`IconPicker`; set and resolver come in as props for the same reason (the component is shared, the
palette is one feature's). No search: the whole set is visible at once. Props `modelValue`
(`string | null`), `colors`, `resolve`, `clearable` (prepends a «Без цвета» tile that emits
`null`), `size`. Selection shows as a ring plus a check glyph — in a grid made of colours, a state
shown only by colour would be lost.

**Composite** `components/IconColorPicker.vue` — icon and colour in one panel, because they are one
plate on the card and are judged together: a preview of that plate sits in the head strip next to
the palette, the icon set with its search fills the body. Built out of the two primitives in a new
`bare` mode (they drop their own tray) so the panel has a single tray rather than two windows side
by side. Two models, `v-model:icon` / `v-model:color`.

The colour reaches the icons on its own: `.color-tones` on the composite's root declares
`--gc-ink` / `--gc-fill`, and `IconPicker`'s selected tile now reads
`var(--gc-ink, var(--accent))`. Standalone it still paints accent (nothing sets the vars); nested,
it inherits the chosen colour. Custom-property inheritance *is* the link between the two halves —
no prop passes between them, and no `:deep()` reaches into another component.

**Design system** — page `/design-system/icon-color-picker` (composite, two variants incl.
`clearable`) and page `/design-system/color-picker` (`controls/ColorPickerView.vue`) on the real
palette: three picker variants plus the icon plate the colour exists for, including the unset case.
Each picker prints its live model under it (`picked = 'teal'` / `optional = null`) — quoted, so a
name reads as the string it is and «без цвета» as `null` rather than as blank space.
Registered in `router/design-system.ts`, `DesignSystemIndexView.vue` and both locale files
(`design-system/ru.json` index/page/section, `ru.json` → `common.color_picker.none`).

Checks: live pass in an isolated browser context — both themes, tile clicks moving `v-model`, the
clear tile returning to `null`, exactly one `aria-pressed` per picker, a colour click re-tinting the
composite's selected icon tile, the standalone `IconPicker` still painting accent. No tests: the
frontend has no vitest suite.

⚠ Pre-existing, not from this work: the console reports one `aria-labelledby` issue per `IconPicker`
instance (Vuetify's search `VTextField`) — three on `/design-system/icon-picker`, which predates
these files.

`vue-tsc --noEmit` clean, `vite build` ok, `web/dist` rebuilt and re-checked on :22040.

> The rebuild was blocked for a while by an unrelated in-flight refactor in the working tree
> (`ResearchesTable.vue` → `ResearchesList.vue`), since `vue-tsc` gates `vite build`; the live
> checks in that window ran on the Vite dev server (:22041), which compiles on demand. It has since
> landed and the build passes.

## Stage two — the colour reaches the group

**Migration edited in place, not chained.** `rem_006_group` now creates `color VARCHAR(32) NOT NULL
DEFAULT ''` right after `icon`. Editing an applied migration is normally forbidden (forward-only),
and the exception holds only because the group tables were never released: the prod DB sits at
`rem_005`, so `rem_006..008` had not run anywhere that matters. The dev DB that *had* them applied
was replaced wholesale in the same step, so no database is left carrying the old shape.

**Dev DB pulled from prod.** `/mnt/store-dev/agents/mcp/urb-research-stable/runtime/dev/app.sqlite3`
→ our `runtime/dev/`, then `migrate upgrade` on top.

- The dev backend was stopped first, and **by pid, not `stop-all.sh`** — that script's
  `pkill -f 'app\.py'` would have taken down the neighbouring stable instance and its MCP shims.
  Confirmed alive afterwards.
- The old dev DB was moved aside to `runtime/dev/app.sqlite3.bak-20260827-074521`, not overwritten.
- Copied through the SQLite **backup API** from a read-only connection, not `cp`: the source is
  written by a live backend. `integrity_check` / `foreign_key_check` clean.
- Arrived at `rem_005` / `wsm_003` / `com_005` with 43 researches and 20 settings rows;
  `migrate upgrade` applied `rem_006..008`, `migrate check` clean, `research_group` carries `color`.

**Backend.** `colors.py` — the canonical ten names, mirroring `icons.py` down to the reasoning (a
name is not validated on write; only the frontend can draw it, and it survives an unknown one).
`GROUP_COLOR_MAX = 32`; `color` in the ORM model, CRUD create/update (soft-clipped like the rest),
`GroupRow`, and the `GroupBody` of both write routes. **Not** on the MCP surface: how a shelf looks
is a human's choice in the interface, which is what `mcp/group.py` already says about `icon`/`sort`.

**Frontend.** `GroupFormDialog` swaps the lone icon picker for `IconColorPicker` (`clearable`, so
«без цвета» is reachable) and sends `color`; the group card and the group page paint their icon with
`groupColorVars(group.color)` on a `.color-tones` element, reading `var(--gc-ink, var(--accent))` —
the pseudo-shelf «Без группы» keeps the accent because nothing sets the vars for it. The form label
became «Иконка и цвет».

**Tests** (+8, module suite 255): CRUD stores/updates/clears the colour and clips it at the column
width; the API round-trips it through create / update / list and accepts `""` as «снять»; and
`test_group_colors.py` mirrors `test_group_icons.py` — palette snapshot, names that fit the column,
and a text-level parity check against the TS registry, the one seam between the two languages.

Live pass on :22040 against the imported prod data: a group created with rocket + rose renders on
the card in rose, reopening the dialog pre-selects both, «без цвета» clears it (DB `color = ''`,
card back to accent). The probe group was deleted afterwards — the imported DB is left as it came,
43 researches and no groups.

## Problems

The first cut resolved the per-theme step with CSS `light-dark()`, which reads `color-scheme` —
and Vuetify declares `color-scheme` on `.v-application` from its own theme class. Measured live:
flipping `data-theme` alone left the ink on the dark step, because the app element still said
`color-scheme: dark`. So the colours would have followed Vuetify's theme while every token follows
ours. Replaced with the `.color-tones` rule keyed off `data-theme`, like the tokens; the reason is
recorded in `main.scss` so it does not get "simplified" back.

## Result

The colour goes end to end: palette → picker → dialog → column → card. The MCP surface is
deliberately untouched (a shelf's look is a human choice), so nothing is pending there.

⚠ Unrelated, in flight in the working tree: `sources_refetch` was changed to take `codes: list[str]`
while `tests/modules/research/test_search_sources.py` still calls it with `code=` — 8 failures in
the full run that predate nothing of this task's files. Left alone.

New: `src/modules/research/colors.py`, `tests/modules/research/test_group_colors.py`, `web/src/shared/colorTones.ts`, `web/src/features/research/constants/groupColors.ts`,
`web/src/components/ColorPicker.vue`, `web/src/components/IconColorPicker.vue`,
`web/src/views/design-system/controls/ColorPickerView.vue`,
`web/src/views/design-system/controls/IconColorPickerView.vue`.
Changed: `src/modules/research/migrations/versions/rem_006_group.py`,
`src/modules/research/{constants,api,dto}.py`, `src/modules/research/models/group.py`,
`src/modules/research/crud/group.py`, `tests/modules/research/{test_group,test_api}.py`,
`web/src/features/research/api.ts`,
`web/src/features/research/components/GroupFormDialog.vue`,
`web/src/features/research/views/{GroupsView,GroupView}.vue`,
`web/src/features/research/locales/ru.json`,
`web/src/components/IconPicker.vue` (`bare` mode + colour-aware selected tile),
`web/src/styles/main.scss`, `web/src/router/design-system.ts`,
`web/src/views/design-system/DesignSystemIndexView.vue`, `web/src/locales/ru.json`,
`web/src/locales/design-system/ru.json`, rebuilt `web/dist/`.
