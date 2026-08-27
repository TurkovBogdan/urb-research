# memory — archive

Retired entries: facts that are no longer load-bearing in `urb-research` (e.g. tied to the legacy application code the core was originally extracted from). Kept for context, not loaded into the live index.

## Entries

- **No single-use intermediate variables** (was `feedback_no_single_use_vars.md`): don't write `_FOO = "value"` then `FOO = _FOO` — inline the value directly. Also for module-level helpers used once (`_NAME = "intercom"` → inline into `name=`/`tags=[...]`; `_HERE = Path(__file__).parent` used only in one path expr). Any var assigned once and referenced once → inline. *Parked here pending a separate review of the rule.*

- **Strict normalization — fail on unknown tokens** (was `feedback_strict_normalization.md`): normalizers for closed dictionaries must `raise ValueError` on an unknown token, never silently return None/skip. Origin: a legacy `_normalize_format` silently dropped the "field work" format (2026-05-07); same applied to `_extract_employment`. Error propagates into `core_tasks.error_text` / `tasks` log → signal to extend the dictionary. Free-text fields (city, company, description) exempt. *Archived: the examples belong to the legacy donor application; no such normalizers exist in `urb-research`. Principle still valid if closed-dictionary normalizers reappear.*
