/**
 * Клиент API модуля research (бэк: /internal/research).
 *
 * Содержимое пишет MCP-сервер; человеку принадлежат полки, переименование и удаление. Иерархия:
 * research → area → source-query (поиск) → source-document (источник); заметки висят
 * на research. Коды приходят с префиксом (RESEARCH@ / AREA@ / QUERY@ / NOTE@ / SOURCE@) —
 * бэк снимает его сам (strip_prefix идемпотентен), в путь кодируем через encodeURIComponent.
 * Даты — SQL-формат (dto.py::DatetimeUTCStr), форматирует shared/utils/date.
 */

import { internalApi, type RequestOptions } from '@/api/client/internal'

const BASE = '/research'

export type SortDir = 'asc' | 'desc'
export type SourceStatus = 'pending' | 'kept' | 'filtered' | 'error'
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
  group_code: string | null
  group_name: string
  // Вид полки едет со строкой: имена из реестров `groupIcons.ts` / `groupColors.ts`, пустые —
  // когда полки нет. Иначе списку пришлось бы держать ещё и справочник полок ради метки.
  group_icon: string
  group_color: string
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
  group_code: string | null
  group_name: string
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

// По чему бэк умеет сортировать реестр (белый список `RESEARCH_SORT_COLUMNS` в crud/research.py):
// две даты и название — колонки таблицы, счётчики — коррелированные подзапросы. Порядок задаёт
// порядок пунктов в выпадающем списке сортировки.
export const RESEARCH_SORT_FIELDS = [
  'created_at',
  'updated_at',
  'title',
  'area_count',
  'query_count',
  'document_kept',
  'document_filtered',
] as const

export type ResearchSortBy = (typeof RESEARCH_SORT_FIELDS)[number]

export interface ListResearchesParams {
  query?: string
  // Полка: код группы, либо пустая строка — только не разложенные по полкам.
  group_code?: string
  sort_by?: ResearchSortBy
  sort_dir?: SortDir
  page?: number
  page_size?: number
}

type QueryValue = string | number | boolean | null | undefined

const seg = (code: string) => encodeURIComponent(code)

export async function listResearches(
  params: ListResearchesParams,
  opts?: RequestOptions,
): Promise<Paged<ResearchListRow>> {
  return internalApi.get<Paged<ResearchListRow>>(`${BASE}/researches`, {
    ...opts,
    query: { ...params } as Record<string, QueryValue>,
  })
}

export async function getResearch(code: string): Promise<ResearchDetail> {
  return internalApi.get<ResearchDetail>(`${BASE}/researches/${seg(code)}`)
}

// Глубокий поиск: где запрос встречается В ТЕЛАХ зон, заметок и в материале источников. Деталь
// отдаёт вложенные сущности скан-слоем, поэтому тела на клиенте искать не по чему — материал
// одного исследования доходит до полутора десятков мегабайт. Возвращаются только коды.
export interface DeepSearchResult {
  areas: string[]
  notes: string[]
  sources: string[]
}

export async function searchResearchBodies(
  code: string,
  query: string,
  opts?: RequestOptions,
): Promise<DeepSearchResult> {
  return internalApi.get<DeepSearchResult>(`${BASE}/researches/${seg(code)}/search`, {
    ...opts,
    query: { q: query },
  })
}

// ── Группы (полки реестра) ────────────────────────────────────────────────────
// Единственная часть research, которую правит пользователь, а не MCP-сервер.

export interface GroupRow {
  code: string
  title: string
  description: string
  // Имя иконки из палитры бэка; рисуется через constants/groupIcons.ts.
  icon: string
  // Имя цвета из палитры бэка; ступени тона — в constants/groupColors.ts.
  color: string
  // Больший sort — выше в списке.
  sort: number
  updated_at: string
}

// Строка списка полок: карточка + сколько исследований на ней лежит (счётчик считает бэк).
export interface GroupListRow extends GroupRow {
  research_count: number
}

// Псевдо-полка «Без группы»: код с пустым хешем. Бэк снимает префикс (strip_prefix идемпотентен),
// получает пустую строку — а она в его фильтрах и означает «только не разложенные». Поэтому
// адрес /research/researches/GROUP@ работает тем же маршрутом, что и обычная полка, без
// отдельного эндпойнта и без спец-значения в query.
export const UNGROUPED_CODE = 'GROUP@'

export interface GroupBody {
  title: string
  description?: string
  icon?: string
  color?: string
  sort?: number
}

export async function listGroups(opts?: RequestOptions): Promise<GroupListRow[]> {
  return internalApi.get<GroupListRow[]>(`${BASE}/groups`, opts)
}

export async function getGroup(code: string, opts?: RequestOptions): Promise<GroupRow> {
  return internalApi.get<GroupRow>(`${BASE}/groups/${seg(code)}`, opts)
}

export async function createGroup(
  body: GroupBody,
  opts?: RequestOptions,
): Promise<GroupRow> {
  return internalApi.post<GroupRow>(`${BASE}/groups`, body, opts)
}

export async function updateGroup(
  code: string,
  body: GroupBody,
  opts?: RequestOptions,
): Promise<GroupRow> {
  return internalApi.put<GroupRow>(`${BASE}/groups/${seg(code)}`, body, opts)
}

// Что делать с исследованиями удаляемой полки: снять с неё, перевесить на другую либо удалить
// вместе с содержимым. Умолчание — самое мягкое: полка это раскладка, её снос не должен уносить
// работу, поэтому «удалить» человек выбирает руками.
export type ResearchesAction = 'detach' | 'move' | 'delete'

export interface DeleteGroupParams {
  researches: ResearchesAction
  /** Куда перевесить; обязателен при researches='move'. */
  move_to?: string | null
}

export async function deleteGroup(
  code: string,
  params?: DeleteGroupParams,
  opts?: RequestOptions,
): Promise<void> {
  await internalApi.del<void>(`${BASE}/groups/${seg(code)}`, undefined, {
    ...opts,
    query: { ...params } as Record<string, QueryValue>,
  })
}

// null — снять исследование с полки.
export async function setResearchGroup(
  researchCode: string,
  groupCode: string | null,
  opts?: RequestOptions,
): Promise<ResearchDetail> {
  return internalApi.put<ResearchDetail>(
    `${BASE}/researches/${seg(researchCode)}/group`,
    { group_code: groupCode },
    opts,
  )
}

export async function deleteResearch(code: string, opts?: RequestOptions): Promise<void> {
  await internalApi.del<void>(`${BASE}/researches/${seg(code)}`, undefined, opts)
}

// ── Переименование ────────────────────────────────────────────────────────────
// Ручки узкие (`.../title`) и отдают свежую деталку целиком: название входит в неё, и страница
// не собирает новое состояние из ответа и старого объекта по кусочкам.

export async function renameResearch(code: string, title: string): Promise<ResearchDetail> {
  return internalApi.put<ResearchDetail>(`${BASE}/researches/${seg(code)}/title`, { title })
}

export async function renameArea(code: string, title: string): Promise<AreaDetail> {
  return internalApi.put<AreaDetail>(`${BASE}/areas/${seg(code)}/title`, { title })
}

export async function renameNote(code: string, title: string): Promise<NoteDetail> {
  return internalApi.put<NoteDetail>(`${BASE}/notes/${seg(code)}/title`, { title })
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

// Повтор получения материала. Скоуп ручки = что именно перекачиваем: у исследования и области
// это все источники без материала (`error`), у одиночного — он сам в любом статусе, и его разбор
// при этом снимается (вердикт был вынесен по прежнему материалу). Отвечают затронутые строки —
// по их новому статусу видно, чем кончилось: `pending` = материал пришёл, `error` = снова нет.

export async function refetchResearchDocuments(
  researchCode: string,
): Promise<SourceDocumentRow[]> {
  return internalApi.post<SourceDocumentRow[]>(
    `${BASE}/researches/${seg(researchCode)}/documents/refetch`,
  )
}

export async function refetchAreaDocuments(areaCode: string): Promise<SourceDocumentRow[]> {
  return internalApi.post<SourceDocumentRow[]>(
    `${BASE}/areas/${seg(areaCode)}/documents/refetch`,
  )
}

export async function refetchSourceDocument(code: string): Promise<SourceDocumentRow> {
  return internalApi.post<SourceDocumentRow>(`${BASE}/source-documents/${seg(code)}/refetch`)
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
