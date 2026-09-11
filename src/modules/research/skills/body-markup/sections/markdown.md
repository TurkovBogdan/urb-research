# Markdown: what renders and what is dropped

The body goes through markdown-it with GitHub-flavoured extensions and is then sanitised. The
sanitiser runs last and drops anything outside its allowlist — silently, without an error.

## Renders

| Construct | Notes |
|---|---|
| headings `#`…`######` | they also build the page outline — see the `structure` section |
| paragraphs | separated by a **blank line**; a single newline is not a line break |
| lists, nested lists | ordered and unordered |
| task lists | `- [ ]` / `- [x]` become real checkboxes (disabled) |
| tables | GFM pipe tables, with per-column alignment |
| blockquote `>` | used here for explanations and caveats |
| `**bold**`, `*italic*`, `~~strike~~` | |
| inline `` `code` `` | renders as a chip — but a code inside it stops being a link |
| fenced code blocks | see below |
| links | `[label](url)` |
| `---` | horizontal rule |

## Does not render

- **Raw HTML** — parsing never allows it, so `<div>`, `<br>`, `<details>`, `<svg>` are gone.
  There is no escape hatch; express it in markdown or not at all.
- **Images** — bodies are rendered with images off. `![alt](url)` produces nothing useful.
- **Bare `www.example.com`** — only URLs with a scheme autolink. Write `https://…` or a
  markdown link. Conversely `app.py` and `README.md` stay plain text, as intended.

## Code fences

Always put the language on the fence — highlighting comes from it:

````
```python
result = await skill_get("body-markup")
```
````

A **one-line** fence renders as a compact chip (no header). A **multi-line** fence gets a header
with the language badge, a line-number toggle and a copy button. So a single command reads
better as a one-liner than as a three-line block with two blank lines inside.

## Tables

A wide table scrolls inside its own box instead of stretching the page, and a cell is capped at
about 60 characters wide. That makes tables good for short values and bad for prose: a
paragraph in a cell will wrap into a tall, unreadable column.

> Rule of thumb: if a cell needs a comma, it probably wants to be a list item instead.
