// Factory for a same-origin JSON client — the shared machinery behind every zone client
// (today only the internal API, `/internal`). A zone differs by config alone: its path
// PREFIX and its policy callbacks. Everything else is identical and lives here once:
//
//  - Calls go only to our own origin via relative paths; credentials default to
//    'same-origin'. Absolute URLs are rejected outright.
//  - Errors follow the backend envelope (`src/core/api/errors.py`): { error, code?, fields? }.
//    Every non-2xx is thrown as a typed `ApiError`. Network/abort/timeout normalize too.
//  - Ответ обязан быть JSON. Редирект НЕ ответ: `redirect: 'manual'` — за ним не идут никогда
//    (запрещать надо на входе, после ответа запрос уже ушёл на чужой адрес), не-JSON тело и
//    неразбираемый JSON тоже отвергаются. Всё это — `ApiError` с кодом `protocol`.
//  - У каждого запроса есть потолок ожидания: иначе зависший бэкенд вешает приложение молча.
//  - Отказ, который экран не показал сам, докладывается через `onError` (см. `shouldReport`).
//
// Слой сессии (CSRF, 401/403, «сессия потеряна») перенесён из донорского портала целиком, но
// у internal-зоны авторизации нет, поэтому он выключен конфигом: `csrf: false` и отсутствие
// `loginPath`/`onUnauthenticated`. Включение CSRF без соответствующей middleware на бэкенде
// добавило бы провальный GET `<prefix>/csrf-cookie` перед КАЖДОЙ записью.
//
// Dev mode: set VITE_API_BASE to the ORIGIN of a backend reachable directly (no Vite proxy),
// e.g. http://localhost:22040. When set, requests go absolute + credentials: 'include'. Empty
// (default, and always in prod where the SPA is same-origin) keeps the strict same-origin path.

export interface ClientConfig {
  /** Zone path prefix prepended to every call, e.g. '/internal'. */
  prefix: string
  /** Backend origin for direct-HTTP dev (VITE_API_BASE); '' for same-origin (prod default). */
  origin?: string
  /**
   * Двойная отправка CSRF-токена на записи: кука `XSRF-TOKEN` → заголовок `X-XSRF-TOKEN`,
   * обновление куки через `<prefix>/csrf-cookie` и один молчаливый повтор на 419. Включать
   * только для зоны, у которой эта проверка есть на бэкенде.
   */
  csrf?: boolean
  /** Куда 401 уводит браузер (адрес входа зоны). Нет входа — не задавать. */
  loginPath?: string
  /** Показать отказ в правах: экран шелла на текущем адресе, без навигации. */
  onForbidden?: () => void
  /**
   * Сессия кончилась (401). Приложение, которое умеет увести на вход СВОИМИ силами, ставит
   * колбэк и получает переход внутри SPA; без него клиент перезагружает страницу на `loginPath`,
   * теряя несохранённый ввод. Аргумент — адрес, на котором человека застали.
   */
  onUnauthenticated?: (returnTo: string) => void
  /**
   * Сессия, наоборот, УЖЕ открыта (409 `already_authenticated` с гость-ручки). Приложение
   * усыновляет её и уводит в кабинет; форме входа про этот случай знать не нужно.
   */
  onAlreadyAuthenticated?: () => void
  /**
   * Показать отказ человеку. Клиент решает, ЧТО докладывать (см. `shouldReport`), приложение —
   * КАК: обычно всплывающим сообщением. Без колбэка отказ остаётся немым.
   */
  onError?: (error: ApiError) => void
  /**
   * Знает ли приложение, что сессии больше нет. Пока это так, запросы к закрытым ручкам не
   * выходят в сеть вовсе: человек, которого выбило, продолжает кликать, и каждый клик иначе
   * тратит общий лимит зоны, возвращаясь 429 вместо честного «войдите заново».
   */
  isSessionLost?: () => boolean
  /** Потолок ожидания ответа, мс. По умолчанию REQUEST_TIMEOUT_MS. */
  timeoutMs?: number
}

/** Потолок ожидания одного запроса. Живых ручек длиннее у нас нет. */
const REQUEST_TIMEOUT_MS = 20_000

/**
 * Коды отказа, которые ставит САМ клиент (у остальных код приходит от бэкенда).
 * `protocol` — ответ не является нашим JSON: редирект, чужой content-type, битое тело.
 */
export type ClientErrorCode = 'network' | 'timeout' | 'aborted' | 'protocol' | 'session_lost'

/** Машинный код 409 «ты уже вошёл» — его разбирает auth-слой, а не человек. */
export const ALREADY_AUTHENTICATED = 'already_authenticated'

// Mirror of backend ErrorBody (src/core/api/errors.py). `fields` — ошибки по полям формы;
// `code` несёт машинный код бэкенда либо один из ClientErrorCode.
export interface ApiErrorBody {
  error: string
  code?: string
  fields?: Record<string, string>
  /** Секунды из заголовка `Retry-After` у 429 — сколько ждать на самом деле. */
  retryAfter?: number
}

// Thrown for every non-2xx response. `status` 0 + code 'network' = transport failure.
export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly fields?: Record<string, string>
  readonly retryAfter?: number

  constructor(status: number, body: ApiErrorBody) {
    super(body.error)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code ?? undefined
    this.fields = body.fields ?? undefined
    this.retryAfter = body.retryAfter
  }
}

/**
 * Докладывать ли отказ человеку. Правило одно на все запросы:
 * 422 — дело формы (там поля), 401/403/409 — смена состояния, её разбирает auth-слой и шелл,
 * отмена вызывающим и уже известная потеря сессии — не новость. Всё остальное всплывает,
 * если вызывающий не сказал `report: false`, потому что показать сам он тогда обязан.
 */
function shouldReport(error: ApiError, opts: RequestOptions): boolean {
  if (opts.report === false) {
    return false
  }

  if (error.status === 401 || error.status === 403 || error.status === 422) {
    return false
  }

  // 404 — «по этому адресу смотреть нечего», и раздел показывает это состоянием на своём месте
  // (`SectionError`). Тост поверх него дублировал бы ту же новость вторым способом.
  if (error.status === 404) {
    return false
  }

  // ⚠️ Молчим только про ОДИН 409 — «ты уже вошёл», его разбирает auth-слой. Остальные 409
  // доменные, и глушить их значит терять отказ.
  if (error.status === 409 && error.code === ALREADY_AUTHENTICATED) {
    return false
  }

  return error.code !== 'aborted' && error.code !== 'session_lost'
}

type QueryValue = string | number | boolean | null | undefined

export interface RequestOptions {
  query?: Record<string, QueryValue>
  // 401 policy: 'redirect' (default) bounces to the zone login; 'throw' lets the caller handle
  // it (auth bootstrap / login form).
  on401?: 'redirect' | 'throw'
  // 403 policy: 'redirect' (default) hands the refusal to the shell; 'throw' lets the caller
  // handle it inline.
  on403?: 'redirect' | 'throw'
  /** `false` — вызывающий показывает отказ сам; по умолчанию его показывает клиент. */
  report?: boolean
  /** Свой потолок ожидания для этого запроса, мс. По умолчанию — общий для зоны. */
  timeoutMs?: number
  /** Ручка входа: работает и без сессии, поэтому стоп-кран потерянной сессии её не держит. */
  allowGuest?: boolean
  signal?: AbortSignal
}

// Verbs returned by the factory. Paths are zone-relative (the prefix is prepended internally).
export interface ApiClient {
  get: <T>(path: string, opts?: RequestOptions) => Promise<T>
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) => Promise<T>
  put: <T>(path: string, body?: unknown, opts?: RequestOptions) => Promise<T>
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) => Promise<T>
  del: <T>(path: string, body?: unknown, opts?: RequestOptions) => Promise<T>
}

// Read a cookie value (URL-decoded): the double-submit header must carry the decoded token.
function readCookie(name: string): string | null {
  const prefix = name + '='
  for (const part of document.cookie ? document.cookie.split('; ') : [])
    if (part.startsWith(prefix)) return decodeURIComponent(part.slice(prefix.length))
  return null
}

// Один сигнал на «истёк потолок» и «отменил вызывающий» — с раздельным диагнозом: аборт по
// таймауту и аборт по воле кода снаружи должны попадать в разные коды ошибки. Готовая пара
// AbortSignal.timeout/any этого не различает, поэтому свой контроллер.
function deadline(ms: number, external?: AbortSignal) {
  const controller = new AbortController()
  let expired = false

  const timer = setTimeout(() => {
    expired = true
    controller.abort()
  }, ms)

  const relay = () => controller.abort()
  if (external) {
    if (external.aborted) controller.abort()
    else external.addEventListener('abort', relay, { once: true })
  }

  return {
    signal: controller.signal,
    expired: () => expired,
    release: () => {
      clearTimeout(timer)
      external?.removeEventListener('abort', relay)
    },
  }
}

// Ответ пришёл, но это не наш JSON. Тело в сообщение не тащим: там бывает целая html-страница.
function protocolError(status: number, what: string): ApiError {
  return new ApiError(status, { error: `API contract violated: ${what}`, code: 'protocol' })
}

// Map an error response to our normalized ApiError body.
async function toApiError(res: Response): Promise<ApiError> {
  const body: ApiErrorBody = { error: res.statusText || `HTTP ${res.status}` }

  // Сколько ждать до следующей попытки — говорит сам сервер, а не наша догадка.
  const retryAfter = Number.parseInt(res.headers.get('retry-after') ?? '', 10)
  if (Number.isFinite(retryAfter)) body.retryAfter = retryAfter

  // Тело читаем один раз строкой: пустой ответ — это нормально (у отказа тела может не быть),
  // а вот НЕПУСТОЕ и не-JSON значит, что отвечал не наш контур (страница прокси, заглушка WAF).
  // Такому отказу ставим `protocol`, иначе человек получит английский `statusText` от чужого узла.
  const text = await res.text().catch(() => '')

  if (text !== '') {
    try {
      const data = JSON.parse(text)
      if (data && typeof data === 'object') {
        if (typeof data.error === 'string' && data.error) body.error = data.error
        if (typeof data.code === 'string') body.code = data.code
        if (data.fields && typeof data.fields === 'object') {
          const fields: Record<string, string> = {}
          for (const [k, v] of Object.entries(data.fields as Record<string, unknown>))
            fields[k] = Array.isArray(v) ? String(v[0]) : String(v)
          body.fields = fields
        }
      }
    } catch {
      body.code = 'protocol'
    }
  }

  return new ApiError(res.status, body)
}

/**
 * Build a JSON client bound to one zone. See ClientConfig / the file header.
 */
export function createClient(config: ClientConfig): ApiClient {
  const ORIGIN = config.origin ?? ''
  const PREFIX = config.prefix
  const CREDENTIALS: RequestCredentials = ORIGIN ? 'include' : 'same-origin'

  function buildUrl(path: string, query?: RequestOptions['query']): string {
    // Hard rule: zone-relative paths only — never let credentials reach another origin,
    // and keep the prefix owned here, not in callers.
    if (/^https?:\/\//i.test(path))
      throw new Error(`api client: absolute URLs are not allowed ('${path}')`)

    const url = ORIGIN + PREFIX + path
    if (!query) return url
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(query))
      if (v !== null && v !== undefined) qs.append(k, String(v))
    const s = qs.toString()
    return s ? `${url}?${s}` : url
  }

  // Обновить CSRF-куку. Под тем же потолком ожидания, что и сам запрос: зависший
  // `/csrf-cookie` иначе блокирует КАЖДУЮ запись бессрочно, а отвечает за него та же зона.
  async function refreshCsrfCookie(signal?: AbortSignal): Promise<void> {
    const clock = deadline(config.timeoutMs ?? REQUEST_TIMEOUT_MS, signal)

    try {
      await fetch(ORIGIN + PREFIX + '/csrf-cookie', { credentials: CREDENTIALS, signal: clock.signal })
    } catch {
      // ignore — the subsequent request will report the true failure
    } finally {
      clock.release()
    }
  }

  async function ensureCsrfCookie(): Promise<void> {
    if (readCookie('XSRF-TOKEN')) return

    await refreshCsrfCookie()
  }

  // Сессии больше нет. Приложение со своим обработчиком уводит на вход внутри SPA (ввод и
  // бандл остаются); зона без входа (`loginPath` не задан) просто отдаёт отказ наружу.
  function handleUnauthenticated(): void {
    if (typeof window === 'undefined') return

    const to = window.location.pathname + window.location.search + window.location.hash

    if (config.onUnauthenticated) {
      config.onUnauthenticated(to)

      return
    }

    if (config.loginPath === undefined) return
    if (window.location.pathname === config.loginPath) return // already there — don't loop
    window.location.assign(`${config.loginPath}?return=${encodeURIComponent(to)}`)
  }

  // Отказ наружу: сначала доложить (если по правилу это наше дело), потом бросить. Единственная
  // точка выхода ошибки из клиента — иначе «показать» и «бросить» разъезжаются по вызывающим.
  function raise(error: ApiError, opts: RequestOptions): never {
    if (config.onError && shouldReport(error, opts)) {
      config.onError(error)
    }

    throw error
  }

  async function request<T>(
    method: string,
    path: string,
    payload?: unknown,
    opts: RequestOptions = {},
    isRetry = false,
  ): Promise<T> {
    // Стоп-кран: сессии нет и приложение это знает — в сеть не идём вовсе. Ручки входа
    // (`allowGuest`) исключены, иначе выбитому человеку нечем было бы войти обратно.
    if (opts.allowGuest !== true && config.isSessionLost?.() === true) {
      raise(new ApiError(0, { error: 'Session lost', code: 'session_lost' }), opts)
    }

    const write = method !== 'GET' && method !== 'HEAD'
    const csrf = config.csrf === true
    if (write && csrf) await ensureCsrfCookie()

    const headers: Record<string, string> = { 'Cache-Control': 'no-cache', Accept: 'application/json' }
    if (write && csrf) {
      const token = readCookie('XSRF-TOKEN')
      if (token) headers['X-XSRF-TOKEN'] = token
    }
    // `manual`: за редиректом не идём НИКОГДА. Иначе агент повторяет POST'ы методом GET, и
    // страница-оболочка приезжает сюда как успешный ответ.
    const clock = deadline(opts.timeoutMs ?? config.timeoutMs ?? REQUEST_TIMEOUT_MS, opts.signal)
    const init: RequestInit = {
      method,
      credentials: CREDENTIALS,
      headers,
      redirect: 'manual',
      signal: clock.signal,
    }

    // Сериализация ВНУТРИ потолка и внутри нормализации: цикл или BigInt в теле — ошибка кода,
    // но наружу она обязана выйти тем же `ApiError`, а не сырым TypeError.
    try {
      if (payload !== undefined) {
        headers['Content-Type'] = 'application/json'
        init.body = JSON.stringify(payload)
      }

      let res: Response
      try {
        res = await fetch(buildUrl(path, opts.query), init)
      } catch (e) {
        // Транспорт не дал ответа. Три разных диагноза, и путать их нельзя: по таймауту и обрыву
        // сети шелл показывает разные экраны, а отмену вызывающим показывать не надо вовсе.
        if (clock.expired()) raise(new ApiError(0, { error: 'Request timed out', code: 'timeout' }), opts)
        if (opts.signal?.aborted) raise(new ApiError(0, { error: 'Request aborted', code: 'aborted' }), opts)
        raise(new ApiError(0, { error: (e as Error)?.message || 'Network error', code: 'network' }), opts)
      }

      // Редирект: тело и заголовки браузер не отдаёт (status 0, type opaqueredirect) — судим по типу.
      if (res.type === 'opaqueredirect') raise(protocolError(0, 'the API answered with a redirect'), opts)

      if (!res.ok) {
        // 419 = CSRF token expired/rotated. Refresh the cookie and retry the write once.
        if (res.status === 419 && write && csrf && !isRetry) {
          await refreshCsrfCookie(clock.signal)

          return request<T>(method, path, payload, opts, true)
        }

        const err = await toApiError(res)

        // Два статуса — не ошибки, а смена состояния сессии, и обрабатываются они здесь, в одной
        // точке: вызывающему остаётся только показать свой шаг, а не разбираться, куда его вести.
        if (err.status === 401 && opts.on401 !== 'throw') handleUnauthenticated()
        else if (err.status === 409 && err.code === ALREADY_AUTHENTICATED) config.onAlreadyAuthenticated?.()
        else if (err.status === 403 && opts.on403 !== 'throw') config.onForbidden?.()

        raise(err, opts)
      }

      // 204 / пустое тело → undefined; иначе только JSON и ничего кроме.
      if (res.status === 204) return undefined as T

      // ⚠️ Чтение тела тоже под потолком: сервер, отдавший заголовки и заглохший на теле, иначе
      // вешает промис навсегда — а на первом запросе это вечный сплэш вместо приложения.
      let text: string
      try {
        text = await res.text()
      } catch (e) {
        if (clock.expired()) raise(new ApiError(0, { error: 'Request timed out', code: 'timeout' }), opts)
        if (opts.signal?.aborted) raise(new ApiError(0, { error: 'Request aborted', code: 'aborted' }), opts)
        raise(new ApiError(0, { error: (e as Error)?.message || 'Network error', code: 'network' }), opts)
      }

      if (text === '') return undefined as T

      if (!(res.headers.get('content-type') ?? '').includes('application/json'))
        raise(protocolError(res.status, 'the response body is not JSON'), opts)

      try {
        return JSON.parse(text) as T
      } catch {
        raise(protocolError(res.status, 'the response body is malformed JSON'), opts)
      }
    } finally {
      clock.release()
    }
  }

  return {
    get:   <T>(path: string, opts?: RequestOptions) => request<T>('GET', path, undefined, opts),
    post:  <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('POST', path, body, opts),
    put:   <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('PUT', path, body, opts),
    patch: <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('PATCH', path, body, opts),
    del:   <T>(path: string, body?: unknown, opts?: RequestOptions) => request<T>('DELETE', path, body, opts),
  }
}
