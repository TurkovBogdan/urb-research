# EDUCATION INDEX

User-facing learning materials. Unlike `docs/` (reference for the agent), these pages
**teach the user** a concept in depth — with worked examples, ideally grounded in this
codebase.

## Rules

- **Create a page ONLY when the user explicitly asks to be taught something AND explicitly
  asks for a learning page.** Never produce these proactively. A passing «I don't get X»
  during normal work is not a request — wait for «объясни и создай страницу» (or similar).
- **Language: Russian.** These are for the user to read (the user reads Russian). The
  structural index stays in English to match the other `AGENTS/*/INDEX.md` files.
- One file per topic: `AGENTS/education/<slug>.md`. Add a row to the inventory below.
- Optimize for understanding, not brevity: motivation → mental model → concrete examples
  from `src/` → common mistakes → exercises/checklist. Show code, name real files.
- Keep examples runnable/verifiable where possible (the user can paste and try them).

## Inventory

| Page | Topic | Created |
|------|-------|---------|
| [lazy-loading.md](lazy-loading.md) | Ленивая загрузка (lazy imports) в Python: что это, зачем для памяти, как делать в этом проекте | 2026-06-05 |
| [session-auth-cookie.md](session-auth-cookie.md) | Как хранится сессия на фронте: httpOnly-cookie + серверная сессия в БД, два TTL, Argon2id, бутстрап через /me | 2026-06-05 |
| [test-coverage.md](test-coverage.md) | Покрытие тестами (pytest-cov): как мерить и читать `Missing`, `-n0` из-за xdist, почему процент обманывает (артефакт async / недостижимый код / line≠branch) | 2026-06-06 |
