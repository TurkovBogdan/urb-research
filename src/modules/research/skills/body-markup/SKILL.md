---
name: body-markup
description: Read before you write or edit a body (research / area / note) — how codes become links, which markdown this app renders, and how to shape a section.
---

# Writing a body

A body is the deliverable. It is rendered in the user's app, not read as raw text, so what you
type either becomes a page a person can navigate or a page that quietly mangles your work.

Three things decide that, and each has a section here:

- `references` — codes turn into clickable pills labelled with the entity's title. This is the
  single most valuable feature of a body and the easiest one to break (a code in backticks is
  dead text). Read this one before your first body.
- `markdown` — what the renderer supports and what it silently drops. Read it before using
  anything beyond headings, paragraphs and lists — tables, code fences, images, raw HTML.
- `structure` — how to shape a body so it reads: what goes first, how headings drive the page
  outline, where explanations belong, and how to keep it editable with `body_add` / `body_edit`.

Read a section with `skill_get('body-markup', section='references')`.

## The short version

If you read nothing else:

1. Write a code plain in the running text — `SOURCE@…`, `AREA@…` — never in backticks, never
   in brackets. It renders as a link labelled with the entity's title, so build the sentence as
   if the title stood there.
2. Cite with codes you actually reviewed and kept. Never invent one.
3. Separate paragraphs with a blank line — a single newline is not a line break here.
4. Images do not render in a body, and raw HTML is dropped. Don't reach for either.
5. Lead with the answer, then the evidence. The user reads the top of the page first.
