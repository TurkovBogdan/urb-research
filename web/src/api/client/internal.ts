// Client for the INTERNAL API (zone `/internal/*`) — the single way the frontend
// talks to our own backend. Distinct on purpose: every call here is prefixed with
// `/internal`, so callers pass zone-relative paths ('/settings/modules'). A separate
// client would handle any future external/public API.
//
//  - We only ever call our own origin via relative paths; credentials default to
//    'same-origin'. Absolute URLs are rejected outright.
//  - Every non-2xx response is the backend envelope { error, code?, fields? } and is
//    thrown as a typed `ApiError`. Network/abort failures normalize to ApiError too.
//
// Dev mode: set VITE_API_BASE to the ORIGIN of a backend reachable directly (no Vite
// proxy), e.g. http://localhost:12200. When set, requests go absolute + credentials:
// 'include'. Empty (the default, and always in prod where the SPA is same-origin)
// keeps the strict path.

const ORIGIN = import.meta.env.VITE_API_BASE ?? ''
const PREFIX = '/internal'
const CREDENTIALS: RequestCredentials = ORIGIN ? 'include' : 'same-origin'

// Mirror of backend ErrorBody (src/core/api/errors.py).
export interface ApiErrorBody {
  error: string
  code?: string
  fields?: Record<string, string>
}

// Thrown for every non-2xx response. `status` 0 + code 'network' = transport failure.
export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly fields?: Record<string, string>

  constructor(status: number, body: ApiErrorBody) {
    super(body.error)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code
    this.fields = body.fields
  }
}

type QueryValue = string | number | boolean | null | undefined

export interface RequestOptions {
  query?: Record<string, QueryValue>
  signal?: AbortSignal
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  // Hard rule: zone-relative paths only — never let the session cookie reach another
  // origin, and keep the `/internal` prefix owned here, not in callers.
  if (/^https?:\/\//i.test(path))
    throw new Error(`internal api: absolute URLs are not allowed ('${path}')`)

  const url = ORIGIN + PREFIX + path
  if (!query) return url
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(query))
    if (v !== null && v !== undefined) qs.append(k, String(v))
  const s = qs.toString()
  return s ? `${url}?${s}` : url
}

async function toApiError(res: Response): Promise<ApiError> {
  let body: ApiErrorBody = { error: res.statusText || `HTTP ${res.status}` }
  try {
    const data = await res.json()
    if (data && typeof data.error === 'string') body = data
  } catch {
    // non-JSON error body — keep the statusText fallback
  }
  return new ApiError(res.status, body)
}

async function request<T>(
  method: string,
  path: string,
  payload?: unknown,
  opts: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { 'Cache-Control': 'no-cache' }
  const init: RequestInit = { method, credentials: CREDENTIALS, headers, signal: opts.signal }
  if (payload !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(payload)
  }

  let res: Response
  try {
    res = await fetch(buildUrl(path, opts.query), init)
  } catch (e) {
    // network failure / abort — normalize so callers only ever catch ApiError.
    throw new ApiError(0, { error: (e as Error)?.message || 'Network error', code: 'network' })
  }

  if (!res.ok) throw await toApiError(res)

  // 204 / empty body → undefined; otherwise parse JSON.
  if (res.status === 204) return undefined as T
  const text = await res.text()
  return (text ? JSON.parse(text) : undefined) as T
}

// Internal-API verbs. Paths are zone-relative ('/internal' is prepended here).
export const internalApi = {
  get:   <T>(path: string, opts?: RequestOptions) => request<T>('GET', path, undefined, opts),
  post:  <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('POST', path, body, opts),
  put:   <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('PUT', path, body, opts),
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('PATCH', path, body, opts),
  del:   <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('DELETE', path, body, opts),
}
