---
title: SwitchPanel in the settings pages + conditional field visibility
date: 2026-08-27
status: completed
description: "Render boolean settings as the SwitchPanel plate on /settings/core and /settings/modules, and work out how far the backend-owned settings schema can drive UI behaviour (e.g. disabling a connector hides its keys)."
tags: [frontend, settings, core_setup, core_connectors]
---

## Task

Two requests in one turn:

1. Integrate the `SwitchPanel` plate (showcased at `/design-system/switch-panel`) into
   `/settings/core` (ENV setup) and `/settings/modules` (runtime module settings).
2. Answer how customizable the settings UI can be given that the schema is backend-owned, and how
   hacky it gets — the motivating example being «disable Grok → hide the Grok fields».

## Baseline (before the change)

- `/settings/modules` — `SettingFieldBool.vue` **already** renders `SwitchPanel`, but with
  `tone="transparent"`, so there is no visible plate: it reads as a bare switch plus caption.
  `SettingField.vue` suppresses the common description below for `kind === 'bool'` because the
  panel carries it in its default slot (task `2026-07-09-settings-bool-field-description-grouping`).
- `/settings/core` — `SetupView.vue` does not know about `SwitchPanel` at all: a raw
  `<VSwitch :label>` with the description rendered as a separate `text-caption` span below, the
  same detached-caption layout that the July task fixed on the modules page.
- The two pages are separate subsystems: ENV (`core_setup`, `.env` + `os.execv` restart, string
  values, groups from `keys.py`) vs runtime settings (`core/settings`, DB-backed, typed field
  classes, hot).

## Conditional visibility — findings

- `core_setup` already ships the mechanism: `keys.py::VisibleWhen(key, equals)` on `SetupField`,
  serialized by `api.py` and evaluated **reactively on the front** against the current form values
  (`SetupView.visibleFields`). That is how the Postgres fields hide under `DB_PROVIDER=sqlite`.
- The runtime settings subsystem (`core/settings/fields.py`) has **no** equivalent — `Field` carries
  no dependency, `_base_ui()` emits none, and `SettingsView` renders every field of a module flat.
  `core_connectors` is therefore one card with 15 fields (7 gateway toggles + 8 keys) in a single
  column with nothing tying a key to its toggle.

## What was done

**SwitchPanel integration (done).** Three edits, frontend only — no backend, no schema change:

- `web/src/components/settings/SettingFieldBool.vue` — dropped `tone="transparent"`, so every bool
  setting on `/settings/modules` now renders as the real grey plate instead of a bare switch.
- `web/src/features/setup/views/SetupView.vue` — the raw `<VSwitch :label>` replaced by
  `SwitchPanel` carrying `title` + `description`; new predicate `hasCaptionBelow(field)` suppresses
  the shared caption below for bool fields (it would otherwise print the description twice), mirroring
  `SettingField.vue::descriptionBelow`.

`vue-tsc --noEmit` exit 0, `pnpm --dir web build` ok, `web/dist` rebuilt. Verified live on :22040 in
an **isolated browser context**: the plate renders on both pages (`WORKER_ENABLED` on the setup page,
all seven gateway toggles on the modules page) with no duplicated caption.

Side observation the screenshot makes obvious: the plate now reads as a *section header* for its
connector, but the API-key field below it is not attached to it in any way — which is exactly the
gap the second question is about.

## Conditional visibility — options (design, not implemented)

Backend stays the sole owner of the schema in all three; the difference is how much the descriptor
carries.

- **A. `visible_when` on `Field`** — port the `core_setup` mechanism verbatim: an optional
  `VisibleWhen(key, equals)` on the base `Field`, emitted by `_base_ui()`, filtered reactively in
  `SettingsView`. `xai_api_key` gets `visible_when=("xai_gateway_enabled", True)` and disappears when
  the toggle is off. ~20 lines back / ~10 front. Not a hack — it is the pattern the sibling page
  already uses.
- **B. Field grouping** — add a `group` (or `section`) to `Field`; the front renders each group as a
  block inside the module card, with a bool field promoted to the block header. Fixes the real
  problem on `core_connectors` (15 fields in one flat column, key not tied to its toggle) and makes A
  natural: the group collapses under its own toggle instead of each key declaring a dependency.
- **C. Per-module Vue component** — a hand-written `CoreConnectorsSettings.vue`. This is the hacky
  one: the schema stops being the single source of truth and every new connector needs a frontend
  edit. Rejected.

Recommendation: B + A (grouping carries the structure, `visible_when` covers the odd one-off
dependency such as `web_scrapper_api_key`, which is optional even when the gateway is on).

## B + A — implemented

The user picked B + A. The schema stays the single source of truth; `/settings/modules` gained no
per-module frontend code.

**Core (`src/core/settings/`)**

- `fields.py` — new frozen dataclass `VisibleWhen(key, equals=True)` (the default covers the common
  «visible while its service is on»), and two attributes on the base `Field`: `group: str = ""` and
  `visible_when: VisibleWhen | None = None`. Both are emitted by `_base_ui()`, so **every** field kind
  carries them for free. All existing call sites pass keyword arguments, so widening the base
  dataclass broke no construction.
- `ListField.ui_descriptor` strips the two new keys from its item descriptor alongside
  `key/label/description/default` — a list item is a value type, not a setting of its own. The
  stripped keys became a named loop instead of four `pop` lines.
- `schema.py` — `_validate_visibility` fail-fast at registration: a condition pointing at an unknown
  key, or at the field itself, is a `ValueError`. A typo would otherwise pass silently and take the
  field off screen forever while its value kept being applied.

**Schemas**

- `core_connectors` — one group per connector (7), each headed by its `*_gateway_enabled` toggle,
  with the keys carrying `visible_when=VisibleWhen("<service>_gateway_enabled")`. The xAI group holds
  two keys (API + Management), both under the same condition.
- `web_search` — grouped into «Движки» (search/fetch engine) and «Ограничения» (the three limits).
  No conditions: nothing there depends on anything.

**Frontend**

- `api.ts` — `group` + `visible_when` on `FieldBase`; the four repeated `Omit<…, 'key' | …>` unions
  collapsed into a named `SettingOwnKeys`.
- `SettingsView.vue` — `splitByGroup` (a block closes at the first field with a different group, so
  schema order *is* screen order — no dictionary, no sort), `toBlock` (promotes a leading `BoolField`
  to the block header and drops the caption, since the toggle's own label already names the block),
  `visible()` (compares against the **form's** current values, not the saved ones), and a
  `moduleBlocks` computed. Blocks whose fields are all hidden and that have no toggle are dropped so
  no empty frame is left.
- CSS: 12px inside a block vs 24px between blocks, and fields under a toggle get a 14px indent plus a
  left rule — the key reads as belonging to that service and visibly leaves with it.

**Docs** — `AGENTS/docs/platform/module-system.md` § *Config vs Settings* gained a *Layout* subsection
(the two attributes, the contiguity requirement, why the condition is evaluated on the front, and the
bool-header rule).

## Verification

`uv run pytest --all` — **605 passed, 3 skipped** (heavy, no `TEST_PG_DSN`); 6 new tests: three on
`validate_schema` (accepts a sibling reference, rejects an unknown key, rejects self-reference) and
three on `ui_descriptor` (carries group/condition, defaults to ungrouped/always-visible, list items
drop both). `vue-tsc --noEmit` exit 0; `web/dist` rebuilt.

Live on :22040 (isolated browser context):

- `GET /internal/core/settings/core_connectors` — all 15 descriptors carry the right group, all 8
  keys carry the right condition.
- The connectors card went from a flat wall of 15 fields to 7 blocks; the five disabled connectors
  show their toggle only, the two enabled ones show their keys indented under it.
- Reactivity without saving: toggling Tavily on in the form revealed its key field, toggling back
  hid it, and the form returned to its original state (nothing was saved).
- Contrast of the new block caption (11px, 600): **6.56** dark / **5.97** light — both over the 4.5
  threshold.

## Known gaps

- Group captions are not routed through `settingText.ts` — they arrive as backend literals like every
  label does, and the connector groups are proper nouns anyway. If the UI ever ships a second
  language, group titles need the same `(module, key)`-style lookup as labels.
- A field hidden while carrying a validation error hides the error with it; the page-level error
  banner still fires. Not worth special-casing until it bites.
