# frontend-api-client.md — internal API client

The single way the frontend talks to our backend. **Use it for every request** — never
call `fetch`/`axios` directly from a feature. Code: `web/src/api/client/internal.ts`.

## Why one client

It centralises three things that must not be re-implemented per feature:

- **`/internal` zone prefix** — owned by the client. Callers pass zone-relative paths
  (`/my-module/things`, `/my-module/things/{id}`); the client prepends `/internal`.
- **Error contract** — every non-2xx is the backend envelope `{ error, code?, fields? }`,
  thrown as a typed `ApiError`. Network/abort failures normalise to `ApiError(0, code:'network')`
  too, so callers only ever catch one type.

## Usage

```ts
import { internalApi, ApiError } from '@/api/client/internal'

const BASE = '/my-module/things'                               // no /internal here

export function listThings(p: Params): Promise<Page> {
  return internalApi.get<Page>(`${BASE}?${new URLSearchParams(...)}`)
}
export function createThing(body: Input): Promise<Thing> {
  return internalApi.post<Thing>(BASE, body)
}
```

Verbs: `get(path, opts?)`, `post/put/patch/del(path, body?, opts?)`. Each is generic in the
response type. `204`/empty body → `undefined`.

### Per-feature convention

Keep one `api.ts` per feature, holding the request functions + their DTO interfaces. The
file declares a `BASE` constant (zone-relative, **without** `/internal`) and exports thin
functions over `internalApi`. Do not put transport/error logic in features — that lives in
the client.

### Handling errors in a view

`ApiError extends Error`, so the canonical view pattern works and surfaces the real
backend message:

```ts
catch (e) {
  error.value = e instanceof Error ? e.message : String(e)
}
```

Read `e.status` / `e.code` / `e.fields` when you need to branch (e.g. field-level form
errors come back in `fields`).

## Request options (`RequestOptions`)

- `query` — record of query params (null/undefined dropped).
- `signal` — `AbortSignal` for cancellation.

## Security posture

- Zone-relative paths only; absolute `http(s)://` URLs are **rejected** so a request can
  never reach a foreign origin. `credentials` defaults to `'same-origin'`.

## Dev mode

Set `VITE_API_BASE` to a backend origin reachable without the Vite proxy (e.g.
`http://localhost:12200`). When set, requests go absolute with `credentials: 'include'`.
Empty (the default, and always in prod where the SPA is same-origin) keeps the strict path.
