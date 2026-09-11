// Клиент настроек интерфейса (бэк: /internal/core/interface). Значения приходят действующие —
// умолчание там, где человек ничего не менял, поэтому доклеивать на фронте нечего.
//
// Все четыре вызова молчаливые (`report: false`): значение к моменту запроса уже применено на
// экране, и тост на каждую настройку был бы шумом на ровном месте. Про упорный отказ докладывает
// сам механизм обмена — `shared/utils/settings-sync`.
import { internalApi } from '@/api/client/internal'

export type SettingType = 'string' | 'number' | 'boolean'

export type SettingValue = string | number | boolean

/** Машинное описание поля: по нему клиент выбирает элемент управления. */
export interface SettingSchema {
  key: string
  type: SettingType
  default: SettingValue
  /** Набор допустимых значений; `null` — ограничен только тип. */
  options: SettingValue[] | null
}

export interface SettingsPayload {
  values: Record<string, SettingValue>
  /** Приходит только по запросу старта (`include_schema`). */
  schema?: SettingSchema[] | null
}

const BASE = '/core/interface/settings'

const SILENT = { report: false } as const

export function fetchSettings(includeSchema = false): Promise<SettingsPayload> {
  return internalApi.get<SettingsPayload>(BASE, {
    ...SILENT,
    query: includeSchema ? { include_schema: true } : undefined,
  })
}

export function saveSettings(values: Record<string, SettingValue>): Promise<SettingsPayload> {
  return internalApi.patch<SettingsPayload>(BASE, { values }, SILENT)
}

/** Сброс к умолчанию: строки исчезают, ответ несёт значения, которыми они заменились. */
export function resetSettings(keys: string[]): Promise<SettingsPayload> {
  return internalApi.post<SettingsPayload>(`${BASE}/reset`, { keys }, SILENT)
}
