# API request zones + route guards (design)

## `src/core/api/` — error contract (current, shipped)

`src/core/api/` is the home for cross-cutting HTTP-API standards (added 2026-06-03). It holds **only** the error contract: `errors.py` + `exceptions.py`; `__init__` exports `ApiError` / `ErrorBody` / `register_exception_handlers`. There is **no `router`** here — the old `system.py` (the core tasks/locks router) was deleted 2026-06-04; `build_internal_zone` no longer includes a core router (zone = `/health` + `/core/settings` + module sub-routers).

**Error contract (whole app):** success bodies stay as-is (HTTP status = source of truth); **only** errors are standardized to `{error, code?, fields?}` (`ErrorBody`) — not the heavy reference/auth envelope.

- `ApiError` (`errors.py`) — raise via status constructors: `ApiError.not_found/forbidden/conflict/validation/...`.
- `register_exception_handlers(app)` (`exceptions.py`) — called in `create_app`; normalizes `ApiError`, bare `HTTPException` (string detail → `error`, dict → message/code/fields), `RequestValidationError` (→ `fields`), and unhandled `Exception` (→ 500, logged). So an existing `raise HTTPException(404,"x")` auto-becomes `{"error":"x"}` — no need to rewrite module raises. Messages in Russian.
- **GOTCHA:** handlers only apply where `register_exception_handlers` ran. Router-level tests that build a bare `FastAPI()` (not `create_app`) must call it themselves, else `ApiError` propagates / `detail` stays native.

**Auth (no module in bare-core):** core knows **nothing** about users — there is no `src/core/api/auth.py`. A principal contract (a leaf `User` DTO + a `current_user` dependency reading `request.state.user`) would live in a future auth-provider module's `guards.py`, next to its `guard_auth` (write half). Core provides only the neutral channel (`request.state`) + `ApiError`; the guard (writes) and `current_user` (reads) are two halves of one contract → both would belong to that provider. **In bare-core no module registers `auth`/`ability`, so the internal-zone default is `allow_all`**; a future auth module flips it back to `["auth"]` and becomes mandatory for the zone. Auth would be a dependency, not middleware (login/health public).

---

> ⚠️ **The design note below is ARCHIVED — superseded by [`router.md`](router.md).** This is the original 2026-06-03 design
> note. The shipped implementation diverged from it: the label/`set_guard` runtime-replacement seam
> below was **not** built. Reality uses a build-time `@guard("kind", *args)` decorator + a shared
> `GuardRegistry` populated declaratively from `Module.guards`, with zone defaults (`internal`→`auth`).
> Read this only for historical decision context; for current behaviour see `router.md`.

Status: **design only** (historical — never implemented as written). Decision date 2026-06-03.
Shares the error standard `{error, code?, fields?}` (`src/core/api/`).

One task, two parts:
1. **Zones** — split the HTTP surface into `internal` / `api` / `webhook`, each a core zone-router that
   collects routes from all modules. Routes carry a protection **label** (`private` by default).
2. **Guard passing** — core ships a default guard per label that just **denies** (secure-by-default, no
   auth logic); a registry lets a future auth module **replace** a label's guard with the real check.

The core knows nothing about users — it only routes, carries the label, and denies by default. All auth
lives in the auth module.

## The three zones (+ infra)

A **zone = (URL prefix, default label, replaceable guard)**.

| Zone | Prefix | Default label | Identity (when implemented) | Caller |
|------|--------|---------------|------------------------------|--------|
| internal | `/internal` | `private` | `User` (session cookie) | the SPA panel + auth endpoints |
| external | `/api` | `private` | `TokenScope` (bearer + TTL) | third-party integrations |
| webhook | `/webhook` | `signed` | none (per-source signature) | inbound webhooks |
| infra | `/health` | `public` | — | liveness probe |

`api`/`webhook` are just laid in now (default-deny guard, no real check yet).

## Task 1 — zones: core zone-routers collect all modules

Core owns one router per zone in explicit files; **modules attach into them** (replacing today's
per-module `app.include_router("/api/<m>")`).

```
src/core/router/
├── __init__.py     # re-exports router_internal / router_api / router_webhook + label markers
├── internal.py     # router_internal = APIRouter()   → mounted at /internal
├── api.py          # router_api      = APIRouter()   → mounted at /api
├── webhook.py      # router_webhook  = APIRouter()   → mounted at /webhook
└── labels.py       # protection labels: private (default) / public / signed + read/attach
```

```python
# in a module (e.g. an auth module)
from src.core.router import router_internal

router_internal.include_router(my_router, prefix="/my-module")   # routes default to `private`
```

```python
# create_app — mount each zone-router once, with the zone guard (see Task 2)
app.include_router(router_internal, prefix="/internal", dependencies=[Depends(route_guard)])
app.include_router(router_api,      prefix="/api",      dependencies=[Depends(route_guard)])
app.include_router(router_webhook,  prefix="/webhook",  dependencies=[Depends(route_guard)])
```

Protection is a **per-route label**, default `private`; `@public` opts a route out (e.g. login):

```python
# src/core/router/labels.py
def public(fn):  fn.__label__ = "public"; return fn      # opt out of protection
def label_of(endpoint) -> str:  return getattr(endpoint, "__label__", "private")   # default = private
```

```python
@router_internal.post("/auth/login")
@public                       # ← reachable without a session
async def login(...): ...

@router_internal.post("/auth/change-password")
async def change_password(...): ...        # no label ⇒ private (protected)
```

Migration (`/api/<module>` is all SPA-internal today → `/internal/<module>`):
1. Backend: each module attaches to `router_internal` instead of `app.include_router("/api/<name>")`;
   move core tasks/locks + settings under `/internal`.
2. Frontend: shared wrapper (`web/src/api/`) owns base `/internal` → 9 `features/*/api.ts` drop the `/api`
   prefix from `BASE`.
3. nginx template: add `location /internal/` and `/webhook/` alongside `/api/` (webhooks: pass body
   through unmodified for signatures).
4. Tests: update prefixes.
5. Infra: `/health` public; OpenAPI `/docs` — one schema, tag routes by zone.

## Task 2 — guard passing: default-deny guard + replaceable registry

The seam by which the core **accepts** a guard/middleware from a module. Core ships a default guard per
label that **denies unconditionally** (so an unprotected app is closed, not open); a future auth module replaces
the `private` (and later `signed`/scope) guard with the real implementation.

```python
# src/core/router/guards.py
from src.core.api import ApiError
from src.core.router.labels import label_of

async def _deny(request):                      # default guard — secure-by-default
    raise ApiError.unauthorized("Auth not configured")

_GUARDS: dict[str, Guard] = {"private": _deny, "signed": _deny}   # label → guard

def set_guard(label: str, guard: Guard) -> None:   # ← the "passing system"
    """Replace a label's guard. Called by the auth module at startup."""
    _GUARDS[label] = guard

async def route_guard(request: Request):           # the zone mount dependency
    lbl = label_of(request.scope["endpoint"])
    if lbl == "public":
        return                                     # public → no check
    await _GUARDS[lbl](request)                    # delegate to the registered guard
```

```python
# the auth module (separate, later) — replaces the default deny with the real check
class AuthModule(Module):
    async def on_startup(self, app):
        set_guard("private", session_guard)        # session-cookie → User → ok / 401 / 403
```

Properties:
- **Secure-by-default**: before the auth module is loaded, `private` routes hit `_deny` → error. Nothing is
  silently open.
- **Core has zero auth logic**: it only reads the label and calls whatever guard is registered.
- **One seam, reused**: same `set_guard` for `signed` (webhook) and scope-based `api` guards later.
- `request.scope["endpoint"]` is populated before dependency resolution, so `route_guard` can read the
  label.

## Single source of zones

`src/core/router/` is the single source of zone prefixes + the guard registry, consumed by the central
mount in `create_app` and later by the nginx config / OpenAPI tagging.

## Open questions

- `/webhook` vs `/webhooks` (singular chosen, matches the request wording).
- External `/api` versioning (`/api/v1/...`) from day one?
- Label vocabulary beyond `private`/`public`/`signed` (e.g. role/scope-parameterized labels like
  `scope("tasks:write")`) — design when the auth module lands.
- Whether the default guard should be `_deny` for ALL zones from the start, or pass-through in dev.
