/**
 * Клиент API модуля доступов (бэк: /internal/connectors + /internal/accesses).
 *
 * Две поверхности: паспорта коннекторов — что вообще можно настроить, и записи доступа —
 * чем мы располагаем. Секрет наружу не приходит никогда: в значениях записи вместо него
 * едет сентинел `NOT_CHANGED`, а в дескрипторе поля — признак `is_set`. Обратно тот же
 * сентинел (или пустая строка) значит «не менял»; стереть поле можно только явным `clear`.
 */

import { internalApi } from '@/api/client/internal'
import type { FieldDescriptor } from '@/features/settings/api'

const CONNECTORS = '/connectors'
const ACCESSES = '/accesses'

/** Секрет не отдаётся наружу — вместо него приходит и уходит этот сентинел. */
export const SECRET_UNCHANGED = 'NOT_CHANGED'

export type AccessStatusCode = 'disabled' | 'unconfigured' | 'undecryptable' | 'error' | 'ok'

/** Паспорт коннектора: что это за сервис и из каких полей состоит доступ к нему. */
export interface ConnectorPassport {
  service: string
  name: string
  description: string
  // Код группы справочника; пустой — карточка уходит в «Прочее».
  group: string
  owner: string
  has_balance: boolean
  fields: FieldDescriptor[]
}

/**
 * Группа справочника: чем сервис является по своей природе.
 *
 * Имя и описание переводятся по коду (`core_connectors.group.<code>.*`) с откатом на
 * литерал бэка, иконка — kebab-имя для `@/shared/icons`.
 */
export interface ConnectorGroup {
  code: string
  name: string
  description: string
  icon: string
}

/** Диагноз записи: первые четыре считаются без сети, `error` — по итогу живой проверки. */
export interface AccessStatus {
  status: AccessStatusCode
  detail: string | null
}

// Одна метрика баланса: денежная величина ИЛИ «использовано из всего».
export interface BalanceMetric {
  label: string
  amount: number | null
  currency: string | null
  used: number | null
  total: number | null
  used_percent: number | null
  unit: string | null
}

// Баланс коннектора: набор доступных метрик (баланс, лимит ключа, кредиты…). error — если не сняли.
export interface ConnectorBalance {
  service: string
  name: string
  metrics: BalanceMetric[]
  error: string | null
}

/** Результат живой проверки доступа. */
export interface ConnectorCheck {
  ok: boolean
  latency_ms: number | null
  error: string | null
}

export interface AccessRow {
  id: number
  enabled: boolean
  connector: string
  connector_name: string
  is_default: boolean
  status: AccessStatus
  created_at: string
  updated_at: string
}

/** Строка + баланс, снятый вживую. Проверка сюда не входит — она по кнопке. */
export interface AccessView extends AccessRow {
  has_balance: boolean
  balance: ConnectorBalance | null
}

/** Запись под форму: значения (секреты — сентинелом) + дескрипторы её полей. */
export interface AccessDetail extends AccessRow {
  values: Record<string, string>
  fields: FieldDescriptor[]
}

export interface AccessPayload {
  enabled?: boolean
  values?: Record<string, string>
  clear?: string[]
}

export async function fetchConnectors(): Promise<ConnectorPassport[]> {
  return internalApi.get<ConnectorPassport[]>(CONNECTORS)
}

export async function fetchConnectorGroups(): Promise<ConnectorGroup[]> {
  return internalApi.get<ConnectorGroup[]>(`${CONNECTORS}/groups`)
}

export async function fetchAccesses(withBalance = false): Promise<AccessView[]> {
  const query = withBalance ? '?with_balance=true' : ''
  return internalApi.get<AccessView[]>(`${ACCESSES}${query}`)
}

export async function fetchAccess(id: number): Promise<AccessDetail> {
  return internalApi.get<AccessDetail>(`${ACCESSES}/${id}`)
}

export async function createAccess(
  connector: string,
  payload: AccessPayload,
): Promise<AccessRow> {
  return internalApi.post<AccessRow>(ACCESSES, { connector, ...payload })
}

export async function updateAccess(id: number, payload: AccessPayload): Promise<AccessRow> {
  return internalApi.put<AccessRow>(`${ACCESSES}/${id}`, payload)
}

export async function deleteAccess(id: number): Promise<void> {
  await internalApi.del<void>(`${ACCESSES}/${id}`)
}

export async function checkAccess(id: number): Promise<ConnectorCheck> {
  return internalApi.post<ConnectorCheck>(`${ACCESSES}/${id}/check`)
}
