---
title: Core API standards — error handling + (mock) current user
date: 2026-06-03
status: in-work  # in-work | completed | deferred
description: "New src/core/api/ package with cross-cutting HTTP-API solutions: a unified error format {error, code?, fields?} via app-wide exception handlers + an ApiError constructor, plus a mock current_user dependency (placeholder for core_auth). First concrete step of the auth work."
tags: [core, api, auth, errors]
---

## Task

Starting the auth work from error handling. The app needs: (1) a convenient constructor of correct
API errors for the rest of the app, (2) a users middleware (mock for now), (3) figure out what else
is needed. A `src/core/api/` package for standard API solutions was the natural home.

## Context

Each module mounts its `APIRouter` under `/api/<module>` from `Module.configure(app, config)` (called
in `create_app`'s build phase). Endpoints raised bare `HTTPException` → responses had no standard shape
(FastAPI native: `{detail: str}` for HTTPException, `{detail: [..]}` for 422, plain text for 500). No
auth existed. Decision (with user): keep success bodies "as-is" (status code = source of truth), and
standardize ONLY errors into a light envelope `{error, code?, fields?}` — not the heavy reference/auth
`{status,code,message,data,meta}` envelope.

## What was done

- `git mv src/core/api.py → src/core/api/system.py` (the core's own tasks/locks endpoints) to free the
  `api` name for a package. `src/core/api/__init__.py` re-exports `router` so existing imports
  (`from src.core.api import router` in app_factory + test) keep working.
- `src/core/api/errors.py` — `ApiError(Exception)` (status_code/message/code/fields) with status
  constructors (`bad_request/unauthorized/forbidden/not_found/conflict/validation/too_many_requests`) +
  `ErrorBody` pydantic model (`{error, code?, fields?}`).
- `src/core/api/exceptions.py` — `register_exception_handlers(app)`: maps `ApiError`,
  Starlette/FastAPI `HTTPException` (string detail → `error`; dict detail → message/code/fields),
  `RequestValidationError` (loc list → `fields`, drops `body/query/path` prefix), and unhandled
  `Exception` (→ 500, logged, neutral message) all to `ErrorBody`.
- `src/core/api/auth.py` — `User` dataclass (id/email/role/abilities[CASL]) + `current_user` FastAPI
  dependency (MOCK: returns a fixed admin; future = read session-cookie → DB lookup) + `require_role(*roles)`
  gate (→ 403). Chose a **dependency**, not middleware (auth is per-route; login/health are public).
- Wired `register_exception_handlers(app)` into `create_app`.
- Migrated the one dict-detail producer: `_settings/api.py` PUT-invalid → `ApiError.validation(...)`.
- Tests: new `tests/core/test_api_errors.py` (7 pure tests: ApiError→envelope, HTTPException string,
  validation→fields, unhandled→500, current_user mock, require_role allow/forbid). Updated 3 existing
  assertions to the new shape (`_settings` ×2, `llm_providers` ×1) and added `register_exception_handlers`
  to those two router-level test app fixtures (they build a bare `FastAPI()`, not `create_app`).
- Verified: `pytest --core` → 169 passed; affected module tests green.

## Result

New package `src/core/api/` (`errors.py`, `exceptions.py`, `auth.py`, `system.py`, `__init__.py`);
`create_app` registers handlers; `_settings/api.py` uses `ApiError`. Error contract for the whole app:
non-2xx → `{error, code?, fields?}`. `current_user`/`require_role` ready for endpoints (mock until
`core_auth`).

### What else is needed (open — item #3)
- Real `core_auth`: `users`/`sessions`/`login_attempts` tables, Argon2id (`pwdlib`), session-cookie,
  `/internal-api/auth/*` + `/account/*` per the reference contract; swap the mock `current_user` body.
- Frontend: the http wrapper (`web/src/api/`) consuming `{error, code?, fields?}` + 401 handling (designed,
  not built — separate decision pending: envelope behavior + whether to migrate existing `features/*/api.ts`).
- uvicorn behind proxy: `--proxy-headers` so `Secure` cookies work behind Cloudflare/nginx.
- Decide default error message language (currently Russian, user-facing) vs English.
