/**
 * Клиент read-API модуля web_search (бэк: /internal/web-search).
 *
 * Только просмотр: списки запросов и страниц (пагинация + фильтры) и детальные
 * (запрос с его выдачей; страница с markdown-контентом). Даты приходят в SQL-формате
 * (см. dto.py::SqlDateTime) — их форматирует shared/utils/date.
 */

import { internalApi } from '@/api/client/internal'

const BASE = '/web-search'

export type QueryStatus = 'pending' | 'processing' | 'done' | 'error'
export type PageStatus = 'pending' | 'processing' | 'done' | 'error'
export type SortDir = 'asc' | 'desc'

export interface Paged<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface QueryRow {
  code: string
  search_engine: string
  fetch_engine: string
  status: QueryStatus
  query: string
  params: Record<string, unknown> | null
  error: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

export interface QueryResultView {
  page_code: string
  rank: number | null
  score: number | null
  summary: string | null
  meta: Record<string, unknown> | null
  page_url: string
  page_title: string | null
  page_domain: string | null
  page_status: PageStatus
  page_fetched_at: string | null
}

export interface QueryDetail extends QueryRow {
  results: QueryResultView[]
}

export interface WebSearchPageRow {
  code: string
  status: PageStatus
  domain: string | null
  url: string
  title: string | null
  body_hash: string | null
  error: string | null
  fetched_at: string | null
  created_at: string
  updated_at: string
}

export interface WebSearchPageDetail extends WebSearchPageRow {
  body: string | null
}

export interface ListQueriesParams {
  query?: string
  status?: QueryStatus | null
  search_engine?: string | null
  sort_by?: string
  sort_dir?: SortDir
  page?: number
  page_size?: number
}

export interface ListPagesParams {
  query?: string
  status?: PageStatus | null
  domain?: string | null
  sort_by?: string
  sort_dir?: SortDir
  page?: number
  page_size?: number
}

type QueryValue = string | number | boolean | null | undefined

export async function listQueries(params: ListQueriesParams): Promise<Paged<QueryRow>> {
  return internalApi.get<Paged<QueryRow>>(`${BASE}/queries`, {
    query: { ...params } as Record<string, QueryValue>,
  })
}

export async function getQuery(code: string): Promise<QueryDetail> {
  return internalApi.get<QueryDetail>(`${BASE}/queries/${encodeURIComponent(code)}`)
}

export async function listPages(params: ListPagesParams): Promise<Paged<WebSearchPageRow>> {
  return internalApi.get<Paged<WebSearchPageRow>>(`${BASE}/pages`, {
    query: { ...params } as Record<string, QueryValue>,
  })
}

export async function getPage(code: string): Promise<WebSearchPageDetail> {
  return internalApi.get<WebSearchPageDetail>(`${BASE}/pages/${encodeURIComponent(code)}`)
}

export interface CreateQueryBody {
  query: string
  search_engine?: string | null
  fetch_engine?: string | null
  max_results?: number | null
}

export interface EnginesInfo {
  search: string[]
  fetch: string[]
  search_default: string
  fetch_default: string
}

// Запуск поиска — fire-and-forget: бэк ставит прогон в фон и сразу отдаёт pending-запрос
// (клиент не ждёт; прогресс виден по обновлению списка pending→processing→done).
export async function createQuery(body: CreateQueryBody): Promise<QueryRow> {
  return internalApi.post<QueryRow>(`${BASE}/queries`, body)
}

// Доступные движки по ролям (включённые в core_connectors) + дефолты — для формы создания.
export async function listEngines(): Promise<EnginesInfo> {
  return internalApi.get<EnginesInfo>(`${BASE}/engines`)
}
