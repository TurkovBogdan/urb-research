/**
 * Клиент API модуля research (бэк: /internal/research).
 *
 * Содержимое пишет MCP-сервер; человеку принадлежат группы, переименование и удаление. Иерархия:
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
  // Вид группы едет со строкой: имена из реестров `shared/icons.ts` / `shared/colors.ts`, пустые —
  // когда группы нет. Иначе списку пришлось бы держать ещё и справочник групп ради метки.
  group_icon: string
  group_color: string
  area_count: number
  query_count: number
  // Источники одной колонкой: всего, а рядом разбор — принятые, отсеянные и не скачавшиеся.
  document_count: number
  document_kept: number
  document_filtered: number
  document_error: number
  created_at: string
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
  // Вид группы, как и у строки списка: имена из реестров `shared/icons.ts` / `shared/colors.ts`,
  // пустые — когда группы нет.
  group_icon: string
  group_color: string
  body: string
  areas: AreaRow[]
  queries: SourceQueryRow[]
  notes: NoteRow[]
  updated_at: string
}

// Путь наверх приезжает с деталкой, а не достаётся из истории переходов: при заходе по прямой
// ссылке истории нет, а вернуться в родителя страница обязана уметь всегда.
export interface AreaDetail {
  code: string
  title: string
  description: string
  objective: string
  scope: string
  expectations: string
  body: string
  research_code: string
  research_title: string
  updated_at: string
}

export interface SourceQueryDetail extends SourceQueryRow {
  research_code: string
  research_title: string
  area_title: string
  documents: SourceDocumentRow[]
}

export interface NoteDetail {
  code: string
  kind: NoteKind
  title: string
  description: string
  body: string
  research_code: string
  research_title: string
  updated_at: string
}

export interface SourceDocumentDetail extends SourceDocumentRow {
  body: string | null
  research_code: string
  research_title: string
  area_code: string
  area_title: string
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
  'document_count',
] as const

export type ResearchSortBy = (typeof RESEARCH_SORT_FIELDS)[number]

/** Незнакомый ключ (правили localStorage, откатили версию) не должен уехать в запрос: бэк на него
    ответит отказом, и список останется пустым без внятной причины. */
export function resolveResearchSortBy(value: string): ResearchSortBy {
  return RESEARCH_SORT_FIELDS.includes(value as ResearchSortBy)
    ? (value as ResearchSortBy)
    : RESEARCH_SORT_FIELDS[0]
}

export function resolveSortDir(value: string): SortDir {
  return value === 'asc' ? 'asc' : 'desc'
}

export interface ListResearchesParams {
  query?: string
  // Слои стога поверх основы. Основа — название и описание — в поиске всегда: ими исследование
  // названо в списке. Каждый слой включается сам по себе; материал источников у бэка выключен по
  // умолчанию (он на порядок больше всего написанного руками).
  in_body?: boolean
  in_areas_and_notes?: boolean
  in_sources?: boolean
  // Группа: её код, либо пустая строка — только не разложенные по группам.
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

// ── Группы (раскладка реестра) ────────────────────────────────────────────────
// Единственная часть research, которую правит пользователь, а не MCP-сервер.

export interface GroupRow {
  code: string
  title: string
  description: string
  // Имя иконки из палитры бэка; рисуется через shared/icons.ts.
  icon: string
  // Имя цвета из палитры бэка; ступени тона — в shared/colors.ts.
  color: string
  // Больший sort — выше в списке.
  sort: number
  updated_at: string
}

// Строка списка групп: карточка + сколько исследований в неё входит (счётчик считает бэк).
export interface GroupListRow extends GroupRow {
  research_count: number
  // Когда в группе последний раз работали = самое свежее обновление среди её исследований;
  // null у пустой. Это НЕ `updated_at` самой группы — та меняется от правки имени или иконки.
  research_updated_at: string | null
}

// Псевдо-группа «Без группы»: код с пустым хешем. Бэк снимает префикс (strip_prefix идемпотентен),
// получает пустую строку — а она в его фильтрах и означает «только не разложенные». Поэтому
// адрес /research/researches/GROUP@ работает тем же маршрутом, что и обычная группа, без
// отдельного эндпойнта и без спец-значения в query.
export const UNGROUPED_CODE = 'GROUP@'

export interface GroupBody {
  title: string
  description?: string
  icon?: string
  color?: string
  sort?: number
}

// По чему бэк умеет сортировать группы (белый список `GROUP_SORT_BY_COLUMNS` в crud/group.py).
// `research_updated_at` и `research_count` — коррелированные подзапросы по исследованиям группы,
// остальное — её собственные колонки. `sort` — ручная позиция, которую человек выставляет в форме
// группы; она осталась ОДНИМ ИЗ ключей, а не единственным порядком. Порядок пунктов здесь задаёт
// порядок в выпадающем списке.
export const GROUP_SORT_FIELDS = [
  'research_updated_at',
  'sort',
  'title',
  'research_count',
  'created_at',
] as const

export type GroupSortBy = (typeof GROUP_SORT_FIELDS)[number]

export function resolveGroupSortBy(value: string): GroupSortBy {
  return GROUP_SORT_FIELDS.includes(value as GroupSortBy)
    ? (value as GroupSortBy)
    : GROUP_SORT_FIELDS[0]
}

export interface ListGroupsParams {
  sort_by?: GroupSortBy
  sort_dir?: SortDir
}

export async function listGroups(
  params: ListGroupsParams = {},
  opts?: RequestOptions,
): Promise<GroupListRow[]> {
  return internalApi.get<GroupListRow[]>(`${BASE}/groups`, { ...opts, query: { ...params } })
}

// Какие группы оставить на странице реестра: бэк ищет в самой группе и во всём тексте входящих
// в неё исследований — включая тела зон и заметок, до которых клиенту не дотянуться. Возвращаются
// только коды: карточки уже загружены, надо знать лишь, какие показать. `ungrouped` — про
// псевдо-группу «Без группы», у которой кода нет.
export interface GroupSearchResult {
  codes: string[]
  ungrouped: boolean
}

export async function searchGroups(
  query: string,
  params?: { in_researches?: boolean },
  opts?: RequestOptions,
): Promise<GroupSearchResult> {
  return internalApi.get<GroupSearchResult>(`${BASE}/groups/search`, {
    ...opts,
    query: { q: query, ...params },
  })
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

// Что делать с исследованиями удаляемой группы: убрать из неё, перевесить в другую либо удалить
// вместе с содержимым. Умолчание — самое мягкое: группа это раскладка, её снос не должен уносить
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

// null — убрать исследование из группы.
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

export async function renameResearch(
  code: string,
  title: string,
  opts?: RequestOptions,
): Promise<ResearchDetail> {
  return internalApi.put<ResearchDetail>(`${BASE}/researches/${seg(code)}/title`, { title }, opts)
}

export async function renameArea(code: string, title: string): Promise<AreaDetail> {
  return internalApi.put<AreaDetail>(`${BASE}/areas/${seg(code)}/title`, { title })
}

export async function renameNote(code: string, title: string): Promise<NoteDetail> {
  return internalApi.put<NoteDetail>(`${BASE}/notes/${seg(code)}/title`, { title })
}

// Описание правится тем же узким способом, что и название: своя ручка на одно поле, в ответе —
// свежая деталка целиком. Пустая строка означает «стереть»: описание необязательно.
export async function editResearchDescription(
  code: string,
  description: string,
): Promise<ResearchDetail> {
  return internalApi.put<ResearchDetail>(
    `${BASE}/researches/${seg(code)}/description`,
    { description },
  )
}

export async function editAreaDescription(
  code: string,
  description: string,
): Promise<AreaDetail> {
  return internalApi.put<AreaDetail>(`${BASE}/areas/${seg(code)}/description`, { description })
}

export async function editNoteDescription(
  code: string,
  description: string,
): Promise<NoteDetail> {
  return internalApi.put<NoteDetail>(`${BASE}/notes/${seg(code)}/description`, { description })
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

// Повтор получения материала — по одному источнику: он сам в любом статусе, и его разбор при этом
// снимается (вердикт был вынесен по прежнему материалу). Отвечает затронутая строка — по её новому
// статусу видно, чем кончилось: `pending` = материал пришёл, `error` = снова нет.
//
// Ручки уровня исследования и области (`POST .../documents/refetch`) у бэкенда есть, но интерфейс
// их не зовёт: «перекачать всё сломанное» — долгий прогон, по итогу которого не видно, что именно
// чинили. Массово это делает агент своим тулом `sources_refetch`.

export async function refetchSourceDocument(code: string): Promise<SourceDocumentRow> {
  return internalApi.post<SourceDocumentRow>(`${BASE}/source-documents/${seg(code)}/refetch`)
}

export async function getNote(code: string): Promise<NoteDetail> {
  return internalApi.get<NoteDetail>(`${BASE}/notes/${seg(code)}`)
}

export async function getSourceDocument(code: string): Promise<SourceDocumentDetail> {
  return internalApi.get<SourceDocumentDetail>(`${BASE}/source-documents/${seg(code)}`)
}

// ── Перенос исследования между установками (.urch) ────────────────────────────

// Выгрузка идёт не клиентом API, а самим браузером: клиент разбирает только JSON, а здесь ответ —
// файл, и его имя (с кириллицей, `filename*=UTF-8''…`) знает лишь сервер. Ссылка отдаёт загрузку
// браузеру целиком, вместе с уважением к этому заголовку. Префикс зоны собирается тем же способом,
// что и у опроса здоровья (`features/about/waitForRestart.ts`).
export function researchExportUrl(code: string): string {
  return `${import.meta.env.VITE_API_BASE ?? ''}/internal${BASE}/researches/${seg(code)}/export`
}

const IMPORT_BASE = `${BASE}/import`

// Разбор и применение читают весь архив: сотня страниц с материалом не укладывается в общий
// потолок ожидания зоны (20 с), и оборванный по нему запрос выглядел бы как отказ бэкенда.
const IMPORT_TIMEOUT_MS = 10 * 60 * 1000

export interface ImportUpload {
  upload_id: string
  file_name: string
  size: number
}

export interface ImportArchive {
  file_name: string
  size: number
  created_at: string
  app_version: string
  format_version: number
  /** Архив снят с ЭТОЙ установки: коды в нём уже здешние, и расхождения ожидаются мелкими. */
  same_install: boolean
}

export interface ImportRoot {
  code: string
  title: string
}

// Сущности архива в порядке показа — от исследования вниз по иерархии, страницы веб-поиска и
// полка в конце. Ключи приходят от бэкенда; перечисление задаёт ТОЛЬКО порядок строк сводки,
// поэтому незнакомый ключ не теряется, а дописывается следом (см. `ImportView`).
export const IMPORT_ENTITIES = [
  'research',
  'areas',
  'notes',
  'source_queries',
  'searches',
  'search_results',
  'sources',
  'pages',
  'group',
] as const

export interface ImportPlanCounts {
  create: number
  update: number
  skip: number
  merge: number
  recode: number
}

/** Запись, которой код в этой базе уже занят: приедет под новым. */
export interface ImportRecoded {
  entity: string
  title: string
  from: string
  to: string
}

export interface ImportUpdating {
  entity: string
  title: string
  code: string
}

export interface ImportDivergedPage {
  code: string
  url: string
}

export interface ImportLocallyNewer {
  entity: string
  code: string
  title: string
}

export interface ImportTruncated {
  entity: string
  code: string
  field: string
}

export interface ImportWarnings {
  /** Ссылки наружу архива: в теле они останутся кодами, которые здесь ничего не открывают. */
  dangling_refs: string[]
  diverged_pages: ImportDivergedPage[]
  locally_newer: ImportLocallyNewer[]
  truncated: ImportTruncated[]
}

export interface ImportPlan {
  archive: ImportArchive
  roots: ImportRoot[]
  counts: Record<string, ImportPlanCounts>
  details: {
    recoded: ImportRecoded[]
    updating: ImportUpdating[]
  }
  warnings: ImportWarnings
}

// Что делать с записью, которая в этой базе уже есть. Умолчание — по времени правки: архив
// переписывает только то, что здесь старше него.
export const IMPORT_MODES = ['newer', 'always', 'never'] as const

export type ImportMode = (typeof IMPORT_MODES)[number]

export interface ImportReportCounts {
  created: number
  updated: number
  skipped: number
  merged: number
}

export interface ImportReport {
  roots: ImportRoot[]
  counts: Record<string, ImportReportCounts>
  /** Сколько ссылок в телах переписано на здешние коды. */
  refs_rewritten: number
  dangling_refs: string[]
  warnings: ImportWarnings
}

export async function uploadImportArchive(
  file: File,
  opts?: RequestOptions,
): Promise<ImportUpload> {
  const form = new FormData()
  form.append('file', file)
  return internalApi.post<ImportUpload>(`${IMPORT_BASE}/upload`, form, {
    timeoutMs: IMPORT_TIMEOUT_MS,
    ...opts,
  })
}

export async function analyzeImport(uploadId: string, opts?: RequestOptions): Promise<ImportPlan> {
  return internalApi.post<ImportPlan>(`${IMPORT_BASE}/${seg(uploadId)}/analyze`, undefined, {
    timeoutMs: IMPORT_TIMEOUT_MS,
    ...opts,
  })
}

export async function applyImport(
  uploadId: string,
  mode: ImportMode,
  opts?: RequestOptions,
): Promise<ImportReport> {
  return internalApi.post<ImportReport>(`${IMPORT_BASE}/${seg(uploadId)}/apply`, { mode }, {
    timeoutMs: IMPORT_TIMEOUT_MS,
    ...opts,
  })
}

/** Снять загруженный архив, не применяя его: место под него держит сервер, а не браузер. */
export async function cancelImport(uploadId: string, opts?: RequestOptions): Promise<void> {
  await internalApi.del<void>(`${IMPORT_BASE}/${seg(uploadId)}`, undefined, opts)
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
