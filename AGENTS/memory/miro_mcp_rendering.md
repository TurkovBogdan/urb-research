---
name: miro-mcp-rendering
description: "Miro MCP — how to render readable content; table cells truncate, use flowchart diagrams for branching reference maps"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 69932c9e-1171-4736-8f4c-0d413056fd6a
---

Miro MCP (server `miro` and `claude_ai_Miro`, board "Semaphore.Core" `uXjVGnsP8fI=`) rendering gotchas, learned building the conversation_insights axes reference:

- **Table cells truncate** long text to one line with «…» (no wrap) and column width is NOT API-settable → tables are unreadable for anything longer than a few words. Avoid `table_create` / DSL `TABLE` for descriptions.
- **`table_create` and `layout_create` TABLE (data_table_format) are flaky** — intermittently fail ("Unable to execute the tool" / "Failed to create data_table_format"); need long backoffs and retries. Other item types (SHAPE/TEXT/diagram) are reliable.
- **`SHAPE` cards (round_rectangle) wrap full text** — readable, but need a parent FRAME and look small at low zoom.
- **Best for a branching reference map** (parent → values → comment): `diagram_create` type `flowchart`, `graphdir LR`. Root = `flowchart-terminator`, value = `flowchart-process`, comment = `flowchart-data`; data nodes auto-size to hold the FULL comment text. Connectors `c <src> - <dst>`. Reliable, no truncation. This is what the user wanted ("mindcard: поле → значения → комментарий").
- **Deletion:** no generic item-delete tool (only `code_widget_delete`). Use `layout_update` with `new_string=""` to delete: `layout_read` the scope first to get exact DSL, then match it. Deleting a FRAME does NOT delete its children — they become top-level orphans with absolute coords; delete them in a second pass.
- **Native Mind Map widget is INVISIBLE to the API** — `layout_read`/`board_list_items` don't return it (skipped, no type), there's no create/edit tool. If the user wants the real Miro Mind Map widget, the ONLY way is **browser automation** (claude-in-chrome): double-click a node to edit text + type; the root's **branch-side `+`** (at the node edge where branches converge, hover to reveal) adds a new sibling branch; a node's own `+` (right side) adds a child. Enter on a selected node EDITS it (not add-sibling); Tab adds a child. Fill comment column **bottom-to-top** so growing lower nodes don't shift the coords of nodes still to be clicked.
- SHAPE bulk-create via `layout_create` 400s if a shape has `size=1` (font too small) or h too small / empty content — use size≥ default and real content; bulk is atomic (one bad shape fails the whole batch).
- **Filling a native Mind Map node via browser — the reliable recipe** (learned the hard way): work at ~100–110% zoom so nodes are large and well-spaced; to edit a node do TWO SEPARATE single clicks (click=select, click again=enter text edit) — NOT a fast `double_click` (often fails to enter edit). If the node already has text, `ctrl+a` then type to replace; if empty, just type. **Critical:** if typing happens while NOT in text-edit mode, the letters become Miro keyboard SHORTCUTS (o=ellipse, etc.) → stray shapes + zoom/selection chaos. Add a sibling branch from root: select root, single-click the `+` on the BRANCH side (right edge where lines converge; hover to reveal) — click it ONCE (double-click spawns two branches). Add a child/comment: select the node, single-click its right-side `+`. Fill the comment column bottom-to-top (growing a node shifts rows below it). `left_click_drag` on empty canvas = rubber-band SELECT, not pan — use `scroll` to navigate. Zoom `+`/`−` buttons and drags are flaky; re-screenshot after each viewport change. Verdict: fillable but slow and finicky; for bulk reference maps prefer API flowcharts.
