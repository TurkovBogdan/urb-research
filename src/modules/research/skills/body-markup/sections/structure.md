# Structure: shaping a body that reads

## Lead with the answer

The user opens the page at the top. Put the conclusion there — what was found, in a few
sentences — and let the evidence follow. A body that opens with methodology makes the reader
scroll to learn whether it is worth scrolling.

For an area body that means: the finding first, then the detail, then the caveats. For a
research body: the answers per area, each pointing at the area by code, then the through-line.

## Headings are the page outline

Headings are extracted and drive the page's navigation, so they are not decoration:

- keep them short and descriptive — they are read out of context, in a list;
- keep them **unique within a body** — `body_edit(action='replace_block', heading='## X')`
  targets a heading, and two identical headings make that edit ambiguous;
- one `#` at the top is unnecessary — the entity's title is already displayed above the body;
  start at `##`.

## Explanations go in a blockquote

Definitions, caveats and the "why" behind a claim are set as a quote, so the reader can tell an
aside from the argument:

```
> Первые два числа деградируют плавно; третье — бинарный отказ запроса.
```

Steps, checklists and the main line of reasoning stay ordinary text. Do not quote a whole
section — a quote that runs longer than a few lines stops reading as an aside.

## Keep it editable

A body grows across many calls, and the editing tools work on anchors:

- `body_add(code, text, position='after', anchor='## Section')` — insert relative to a unique
  string, usually a heading;
- `body_edit(code, action='replace', find=…)` — the `find` must occur exactly **once**, or the
  call fails;
- `body_edit(code, action='replace_block', heading='## Section')` — replaces the whole block up
  to the next heading of the same or higher level.

So a body built from named, unique sections stays cheap to amend, while one long undivided
stream forces you to rewrite it whole with `*_update`.

## Length

Write what the material supports. An area body that says less than its brief promised is a
signal that the area needs more searching, not more words — and padding it hides that signal
from both you and the user.
