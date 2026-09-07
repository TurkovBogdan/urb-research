// Обмен настройками интерфейса с базой: гидрация, очередь, дебаунс и флаг «применяем извне».
// Вся сетевая логика собрана здесь, а не размазана по стору — стор остаётся набором ref'ов.
//
// Правило, из которого следует всё остальное: источник истины — база, localStorage остаётся
// кешем. Кеш красит страницу до первого кадра, поэтому запрос на этом месте означал бы вспышку
// чужого оформления; гидрация идёт ПОСЛЕ монтирования и ничего не блокирует (backend, поднятый
// MCP-шимом, отвечает не сразу, и блокирующий запрос превратил бы старт в неподвижный сплэш).
import { ref, type Ref } from 'vue'

import { ApiError } from '@/api/client/internal'
import {
  fetchSettings,
  resetSettings,
  saveSettings,
  type SettingSchema,
  type SettingValue,
} from '@/api/interface-settings'
import { pushToast } from '@/composables/useToasts'
import { i18n } from '@/plugins/i18n'
import type { Codec } from './persisted'

/** Служебные ключи кеша носят точку — настройки реестра её не носят и не спутаются с ними. */
const PENDING_KEY = 'sync.pending'
const IMPORT_MARKER = 'sync.imported'

const DEBOUNCE_MS = 450

/** Сколько подряд неудачных отправок терпим молча, прежде чем сказать человеку. */
const FAILURES_BEFORE_TOAST = 3

/** Старые точечные имена в кеше браузера → ключи реестра. Нужны ровно один раз, при переезде. */
const LEGACY_KEYS: Record<string, string> = {
  'app.theme': 'interface_theme',
  'app.font.interface': 'interface_font',
  'app.font.reading': 'interface_font_reading',
  'app.font.reading_size': 'interface_font_reading_size',
  'app.font.reading_measure': 'interface_font_reading_measure',
  'app.font.mono': 'interface_font_mono',
  'app.font.diagram': 'interface_font_diagram',
  'app.diagram.align': 'interface_diagram_align',
  'app.diagram.max_height': 'interface_diagram_max_height',
  'app.list.research_view': 'interface_list_research_view',
  'app.nav.document': 'interface_nav_document',
  'app.sidebar_collapsed': 'interface_sidebar_collapsed',
}

interface Synced {
  state: Ref<SettingValue>
  fallback: SettingValue
  codec: Codec<never>
}

const synced = new Map<string, Synced>()
const pending = new Set<string>(pendingFromCache())

/** Схема полей: тип, умолчание и набор допустимых значений. Пуста, пока не пришла гидрация. */
export const settingsSchema = ref<SettingSchema[]>([])

let applyingExternal = false
let sending = false
let failures = 0
let timer: ReturnType<typeof setTimeout> | undefined

export function registerSetting<T extends SettingValue>(
  key: string,
  state: Ref<T>,
  fallback: T,
  codec: Codec<T>,
): void {
  synced.set(key, {
    state: state as Ref<SettingValue>,
    fallback,
    codec: codec as unknown as Codec<never>,
  })
}

/** Применяем значение, пришедшее из базы: изменение ref'а в этот момент отправлять обратно не надо. */
export function isApplyingExternal(): boolean {
  return applyingExternal
}

export function enqueue(key: string): void {
  pending.add(key)
  writePending()
  schedule()
}

function schedule(): void {
  clearTimeout(timer)
  timer = setTimeout(() => void flush(), DEBOUNCE_MS)
}

/**
 * Отправить накопленное. Изменённые значения уходят картой, вернувшиеся к умолчанию — списком
 * на сброс: строка, равная дефолту, в базе не хранится.
 *
 * Очередь очищается только после успеха. Отказ не всплывает на каждую настройку — значение уже
 * применено, чинить человеку нечего; про упорный отказ говорим один раз.
 *
 * Отвергнутое сервером снимается с очереди сразу: пачка применяется целиком, поэтому одно
 * негодное значение (испорченный кеш, набор, сузившийся с прошлой выкладки) держало бы в
 * очереди и все остальные ключи — вечно и с тостом каждую третью попытку.
 */
export async function flush(): Promise<void> {
  if (sending || pending.size === 0) return
  const sent = new Map<string, SettingValue>()
  const values: Record<string, SettingValue> = {}
  const resets: string[] = []

  for (const key of pending) {
    const entry = synced.get(key)
    if (!entry) continue
    sent.set(key, entry.state.value)
    if (entry.state.value === entry.fallback) resets.push(key)
    else values[key] = entry.state.value
  }

  sending = true
  // Взводить дебаунс заново стоит только после разобранной пачки: очередь, оставшаяся после
  // сетевого отказа, ждёт следующего движения человека или старта, а не долбится в тот же
  // погашенный backend каждые полсекунды.
  let queueMoved = false
  try {
    if (Object.keys(values).length > 0) await saveSettings(values)
    if (resets.length > 0) await resetSettings(resets)
    // Снимаем с очереди только то, что успели отправить в этом виде: настройка, переставленная
    // ещё раз, пока запрос был в пути, иначе осталась бы в кеше и не доехала до базы.
    const settled = [...sent]
      .filter(([key, value]) => synced.get(key)?.state.value === value)
      .map(([key]) => key)
    dropFromQueue(settled)
    failures = 0
    queueMoved = true
  } catch (error) {
    const refused = rejectedKeys(error)
    if (refused.length === 0) failed()
    else {
      dropFromQueue(refused)
      queueMoved = true
    }
  } finally {
    sending = false
    // Пока запрос был в пути, дебаунс мог отработать вхолостую — сорванное им изменение иначе
    // ждало бы следующего движения человека или перезагрузки страницы.
    if (queueMoved && pending.size > 0) schedule()
  }
}

/** Ключи, которые сервер назвал негодными (422 с картой полей); пусто — отказ не про них. */
function rejectedKeys(error: unknown): string[] {
  if (!(error instanceof ApiError) || error.status !== 422) return []
  return Object.keys(error.fields ?? {}).filter((key) => pending.has(key))
}

function dropFromQueue(keys: string[]): void {
  for (const key of keys) pending.delete(key)
  writePending(keys)
}

function failed(): void {
  failures += 1
  if (failures < FAILURES_BEFORE_TOAST) return
  failures = 0
  pushToast(i18n.global.t('settings.interface.sync.failed'), 'warn')
}

/**
 * Старт обмена: досылаем неотправленное, забираем значения вместе со схемой, при первом запуске
 * переносим накопленное в браузере.
 *
 * Порядок важен: сначала очередь (иначе ответ базы откатил бы изменение, сделанное в прошлый
 * заход и не дошедшее), потом чтение.
 */
export async function startSettingsSync(): Promise<void> {
  if (typeof window !== 'undefined') {
    // Уход со страницы не должен стоить последнего изменения: дебаунс не успевает,
    // а `visibilitychange` — единственное событие, которое браузер даёт надёжно.
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') void flush()
    })
    window.addEventListener('pagehide', () => void flush())
  }

  await flush()

  const payload = await fetchSettings(true).catch(() => null)
  if (payload === null) return

  applyExternal(payload.values)
  settingsSchema.value = payload.schema ?? []
  await importLegacyKeys(payload.values)
}

/** Значения из базы в ref'ы. Ключи, чьё изменение ещё не доехало, не трогаем — иначе откат на глазах. */
function applyExternal(values: Record<string, SettingValue>): void {
  applyingExternal = true
  try {
    for (const [key, value] of Object.entries(values)) {
      const entry = synced.get(key)
      if (!entry || pending.has(key)) continue
      if (entry.state.value !== value) entry.state.value = value
    }
  } finally {
    applyingExternal = false
  }
}

/**
 * Одноразовый перенос настроек, накопленных в браузере до появления модуля.
 *
 * Идёт только после успешного ответа: маркер и удаление старых ключей при недоступном бэкенде
 * стёрли бы выбор человека. Ключ, по которому у базы уже есть своё мнение, не трогаем — там
 * настройка, сделанная в другом браузере, и она новее нашего наследия.
 */
async function importLegacyKeys(serverValues: Record<string, SettingValue>): Promise<void> {
  if (typeof localStorage === 'undefined' || localStorage.getItem(IMPORT_MARKER) !== null) return

  const carried: Record<string, SettingValue> = {}
  for (const [legacyKey, key] of Object.entries(LEGACY_KEYS)) {
    const raw = localStorage.getItem(legacyKey)
    const entry = synced.get(key)
    if (raw === null || entry === undefined) continue
    const value = (entry.codec as unknown as Codec<SettingValue>).parse(raw)
    const untouchedOnServer = serverValues[key] === entry.fallback
    if (value !== entry.fallback && untouchedOnServer) carried[key] = value
  }

  try {
    if (Object.keys(carried).length > 0) applyExternal((await saveSettings(carried)).values)
  } catch {
    return
  }

  localStorage.setItem(IMPORT_MARKER, '1')
  for (const legacyKey of Object.keys(LEGACY_KEYS)) localStorage.removeItem(legacyKey)
}

function pendingFromCache(): string[] {
  if (typeof localStorage === 'undefined') return []
  const raw = localStorage.getItem(PENDING_KEY)
  if (raw === null) return []
  try {
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((key): key is string => typeof key === 'string') : []
  } catch {
    return []
  }
}

// Очередь живёт в том же кеше: закрытая внутри дебаунса вкладка и погашенный backend не
// теряют изменение — его дошлют при следующем открытии.
//
// Запись идёт слиянием, а не заменой: хранилище общее на все вкладки, и вкладка, выложившая
// туда свой набор целиком, стёрла бы неотправленное соседней. Уходит из очереди только то,
// что названо явно, — разобранное этой вкладкой.
function writePending(settled: string[] = []): void {
  if (typeof localStorage === 'undefined') return
  const queued = new Set([...pendingFromCache(), ...pending])
  for (const key of settled) queued.delete(key)
  if (queued.size === 0) localStorage.removeItem(PENDING_KEY)
  else localStorage.setItem(PENDING_KEY, JSON.stringify([...queued]))
}
