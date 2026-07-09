/**
 * Клиент read-API модуля research (бэк: /internal/research).
 *
 * Только просмотр. Пишет данные MCP-сервер, не эти ручки. Иерархия:
 * research → area → source-query (поиск) → source-document (источник); заметки висят
 * на research. Коды приходят с префиксом (RESEARCH@ / AREA@ / QUERY@ / NOTE@ / SOURCE@) —
 * бэк снимает его сам (strip_prefix идемпотентен), в путь кодируем через encodeURIComponent.
 * Даты — SQL-формат (dto.py::DatetimeUTCStr), форматирует shared/utils/date.
 */

import { internalApi } from '@/api/client/internal'

const BASE = '/research'

export type SortDir = 'asc' | 'desc'
export type SourceStatus = 'pending' | 'kept' | 'filtered' | 'fetch_error'
export type NoteKind = 'result' | 'idea' | 'question' | 'memory' | 'decision' | 'clarification'

export interface Paged<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ── Строки (скан-слой списков) ────────────────────────────────────────────────

export interface ResearchListRow {
  code: string
  title: string
  description: string
  area_count: number
  query_count: number
  document_kept: number
  document_filtered: number
  updated_at: string
}

export interface AreaRow {
  code: string
  title: string
  description: string
  updated_at: string
}

export interface SourceQueryRow {
  code: string
  area_code: string
  query: string
}

export interface NoteRow {
  code: string
  kind: NoteKind
  title: string
  description: string
  updated_at: string
}

export interface SourceDocumentRow {
  code: string
  status: SourceStatus
  url: string | null
  title: string | null
  summary: string
  note: string
  relevance: number | null
  updated_at: string
}

// ── Детали ────────────────────────────────────────────────────────────────────

export interface ResearchDetail {
  code: string
  title: string
  description: string
  body: string
  areas: AreaRow[]
  queries: SourceQueryRow[]
  notes: NoteRow[]
  updated_at: string
}

export interface AreaDetail {
  code: string
  title: string
  description: string
  objective: string
  scope: string
  expectations: string
  body: string
  updated_at: string
}

export interface SourceQueryDetail extends SourceQueryRow {
  documents: SourceDocumentRow[]
}

export interface NoteDetail {
  code: string
  kind: NoteKind
  title: string
  description: string
  body: string
  updated_at: string
}

export interface SourceDocumentDetail extends SourceDocumentRow {
  body: string | null
}

// ── Эндпойнты ─────────────────────────────────────────────────────────────────

export interface ListResearchesParams {
  query?: string
  sort_dir?: SortDir
  page?: number
  page_size?: number
}

type QueryValue = string | number | boolean | null | undefined

const seg = (code: string) => encodeURIComponent(code)

export async function listResearches(
  params: ListResearchesParams,
): Promise<Paged<ResearchListRow>> {
  return internalApi.get<Paged<ResearchListRow>>(`${BASE}/researches`, {
    query: { ...params } as Record<string, QueryValue>,
  })
}

export async function getResearch(code: string): Promise<ResearchDetail> {
  return internalApi.get<ResearchDetail>(`${BASE}/researches/${seg(code)}`)
}

export async function getArea(code: string): Promise<AreaDetail> {
  return internalApi.get<AreaDetail>(`${BASE}/areas/${seg(code)}`)
}

export async function getSourceQuery(code: string): Promise<SourceQueryDetail> {
  return internalApi.get<SourceQueryDetail>(`${BASE}/source-queries/${seg(code)}`)
}

export async function listAreaQueries(areaCode: string): Promise<SourceQueryRow[]> {
  return internalApi.get<SourceQueryRow[]>(`${BASE}/areas/${seg(areaCode)}/queries`)
}

export async function listAreaDocuments(areaCode: string): Promise<SourceDocumentRow[]> {
  return internalApi.get<SourceDocumentRow[]>(`${BASE}/areas/${seg(areaCode)}/documents`)
}

export async function listResearchDocuments(researchCode: string): Promise<SourceDocumentRow[]> {
  return internalApi.get<SourceDocumentRow[]>(`${BASE}/researches/${seg(researchCode)}/documents`)
}

export async function getNote(code: string): Promise<NoteDetail> {
  return internalApi.get<NoteDetail>(`${BASE}/notes/${seg(code)}`)
}

export async function getSourceDocument(code: string): Promise<SourceDocumentDetail> {
  return internalApi.get<SourceDocumentDetail>(`${BASE}/source-documents/${seg(code)}`)
}

// Разрешение ссылок-кодов из тела (TYPE@hash) в заголовки сущностей (батч). code — префиксный.
export interface CodeLabel {
  code: string
  title: string | null
}

export async function resolveReferences(codes: string[]): Promise<CodeLabel[]> {
  if (codes.length === 0) return []
  return internalApi.post<CodeLabel[]>(`${BASE}/references`, { codes })
}
