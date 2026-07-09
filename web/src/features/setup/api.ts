/**
 * Клиент API настроек окружения (бэк: /internal/core/setup, модуль core_setup).
 *
 * Редактирует слой ENV/.env: значения — строки, применяются перезапуском процесса
 * (PUT пишет .env и инициирует os.execv-рестарт). Отдельно от рантайм-настроек
 * (/core/settings), которые применяются горячо.
 */

import { internalApi } from '@/api/client/internal'

export type SetupFieldType = 'str' | 'int' | 'bool' | 'choice'

export interface VisibleWhen {
  key: string
  equals: string
}

export interface SetupField {
  key: string
  type: SetupFieldType
  label: string
  description: string
  choices: string[]
  secret: boolean
  value: string
  visible_when: VisibleWhen | null
}

export interface SetupGroup {
  group: string
  fields: SetupField[]
}

export interface SetupPayload {
  groups: SetupGroup[]
}

export interface ApplyResult {
  status: string
  applied: string[]
}

const BASE = '/core/setup'

export async function getSetup(): Promise<SetupPayload> {
  return internalApi.get<SetupPayload>(BASE)
}

export async function applySetup(values: Record<string, string>): Promise<ApplyResult> {
  return internalApi.put<ApplyResult>(BASE, { values })
}

export async function isBackendUp(): Promise<boolean> {
  try {
    await internalApi.get('/health')
    return true
  } catch {
    return false
  }
}
