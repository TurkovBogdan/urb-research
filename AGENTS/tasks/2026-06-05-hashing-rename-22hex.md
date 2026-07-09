---
title: Rename hashing helpers + switch to 22-hex SHA-256
date: 2026-06-05
status: completed
description: "Rename content_hash→text_hash and fingerprint_dict→dict_hash; both now emit 22-char lowercase hex (SHA-256[:22], 88-bit) instead of mixed encodings, dropping the '_'/'-' from base64url. Widen the version columns 16→22 via migrations."
tags: [core, hashing, conversations, conversation_insights, mail_sync, intercom]
---

## Task

User disliked the `_`/`-` chars in `content_hash` (base64url). Decision after discussion:
rename `content_hash` → `text_hash`, `fingerprint_dict` → `dict_hash`, unify both on a
**22-char lowercase-hex** output (SHA-256 hexdigest[:22] = 88-bit), add collision-probability
comments in code, find every usage, and add migrations widening the affected DB columns to 22.

## Context

- `content_hash` was BLAKE2b-128 → base64url (22 chars, alphabet `[A-Za-z0-9_-]`).
- `fingerprint_dict` was SHA-256 → hexdigest[:16] (16 chars, `[0-9a-f]`, 64-bit), used for the
  `*_version` freshness fingerprints.
- Goal: clean `[0-9a-f]` alphabet everywhere, same 22-char width (no schema change for
  content_hash columns), more entropy than the old 16-hex (88-bit @ 22 hex).

## What was done

- **`src/core/utils/hashing.py`** rewritten: `_HASH_LEN=22`, shared `_hex()` (SHA-256
  hexdigest[:22]); `dict_hash(params)` (sorted canonical) + `text_hash(text)`; collision-probability
  comment (88-bit, birthday point ~6.6e13). `None`/"" still collapse. base64 import dropped.
- **Call-site rename** (all in `src`): `dict_hash` — conversation_insights `constants.py`
  (AGENT_VERSION) + `services/tagger_version.py`, mail_sync `services/mail_filter.py` +
  `services/content_hash.py`, intercom `services/body_parser.py`, both conversations providers
  PARSER_VERSION. `text_hash` — conversations providers `intercom.py`/`mail_sync.py` (message +
  aggregate hashes; the `content_hash=` kwarg / `.content_hash` attribute kept).
- **Model columns widened 16→22** + comments refreshed: conversations `parser_version`,
  conversation_insight_results `agent_version`/`tagger_version`, intercom_conversations
  `parser_version`. content_hash columns already String(22). mail_sync content_hash/filter_version
  are unbounded `String` → untouched.
- **Migrations** (alter 16→22, reversible): `conversations/c11_widen_hash_columns`,
  `conversation_insights/ci07_widen_version_columns`, `intercom/i06_widen_parser_version`.
- **Tests**: rewrote `tests/core/utils/test_hashing.py` (text_hash/dict_hash, 22-len, hex-alphabet);
  fixed 2 function imports (test_message.py, test_intercom.py) + 5 length asserts (16→22) in
  mail_sync filter/version/content_hash tests + conversation_insights tagger_version test.

## Problems

5 module tests asserted the old length 16 (mail_sync filter_version/content_hash + tagger_version);
updated to 22. No other 16-length asserts remained (grep-checked).

## Result

- Verified: `test_hashing` 9 passed; `migrate check` shows the 3 new migrations pending and heads
  chain cleanly; affected-module suite 775 passed after fixes; heavy migration tests (conversations,
  conversation_insights, intercom) 2 passed.
- **Caveat (expected)**: hash representation changed → all stored content_hash/version values
  mismatch on first run → one-off mass re-process/re-tag of conversations + insights.
- Migrations not yet applied to dev DB (DB_AUTO_MIGRATE=false); user applies via `migrate upgrade`.
