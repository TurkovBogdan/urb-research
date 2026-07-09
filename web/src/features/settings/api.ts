/**
 * Клиент HTTP API подсистемы settings (бэк: /internal/core/settings).
 *
 * Поля приходят как union-тип по `kind`. Значения хранятся в модуле как
 * объект `key → value`; на PUT мы шлём raw value, бэк сам валидирует.
 */

import { internalApi } from '@/api/client/internal'

export type FieldKind =
  | 'int'
  | 'float'
  | 'bool'
  | 'str'
  | 'date'
  | 'datetime'
  | 'choice'
  | 'multichoice'
  | 'list'

interface FieldBase {
  key: string
  kind: FieldKind
  label: string
  description: string
  default: unknown
}

export interface IntFieldDescriptor extends FieldBase {
  kind: 'int'
  min: number | null
  max: number | null
}

export interface FloatFieldDescriptor extends FieldBase {
  kind: 'float'
  min: number | null
  max: number | null
  step: number
  decimals: number
}

export interface BoolFieldDescriptor extends FieldBase {
  kind: 'bool'
}

export interface StrFieldDescriptor extends FieldBase {
  kind: 'str'
  min_length: number | null
  max_length: number | null
  pattern: string | null
  lines: number
  secret: boolean
  // Только для secret-полей: задан ли токен (сам он наружу не отдаётся).
  is_set?: boolean
}

export interface DateFieldDescriptor extends FieldBase {
  kind: 'date'
  min: string | null
  max: string | null
}

export interface DateTimeFieldDescriptor extends FieldBase {
  kind: 'datetime'
  min: string | null
  max: string | null
}

export interface ChoiceOption {
  code: string
  label: string
}

export interface ChoiceFieldDescriptor extends FieldBase {
  kind: 'choice'
  options: ChoiceOption[]
}

export interface MultiChoiceFieldDescriptor extends FieldBase {
  kind: 'multichoice'
  options: ChoiceOption[]
  min_items: number
  max_items: number | null
}

// Item-дескриптор внутри ListField — без key/label/description/default
// (они стрипаются на бэке в `ui_descriptor`).
export type ListItemDescriptor =
  | Omit<IntFieldDescriptor, 'key' | 'label' | 'description' | 'default'>
  | Omit<FloatFieldDescriptor, 'key' | 'label' | 'description' | 'default'>
  | Omit<StrFieldDescriptor, 'key' | 'label' | 'description' | 'default'>
  | Omit<DateFieldDescriptor, 'key' | 'label' | 'description' | 'default'>
  | Omit<DateTimeFieldDescriptor, 'key' | 'label' | 'description' | 'default'>
  | Omit<ChoiceFieldDescriptor, 'key' | 'label' | 'description' | 'default'>

export interface ListFieldDescriptor extends FieldBase {
  kind: 'list'
  min_items: number
  max_items: number | null
  item: ListItemDescriptor
}

export type FieldDescriptor =
  | IntFieldDescriptor
  | FloatFieldDescriptor
  | BoolFieldDescriptor
  | StrFieldDescriptor
  | DateFieldDescriptor
  | DateTimeFieldDescriptor
  | ChoiceFieldDescriptor
  | MultiChoiceFieldDescriptor
  | ListFieldDescriptor

export interface ModulePayload {
  module: string
  description: string
  fields: FieldDescriptor[]
  values: Record<string, unknown>
}

const BASE = '/core/settings'

export async function listModules(): Promise<ModulePayload[]> {
  return internalApi.get<ModulePayload[]>(`${BASE}/modules`)
}

export async function putValue(
  module: string,
  key: string,
  value: unknown,
): Promise<Record<string, unknown>> {
  const data = await internalApi.put<{ values: Record<string, unknown> }>(
    `${BASE}/${module}/${key}`,
    { value },
  )
  return data.values
}

export async function resetValue(
  module: string,
  key: string,
): Promise<Record<string, unknown>> {
  const data = await internalApi.post<{ values: Record<string, unknown> }>(
    `${BASE}/${module}/${key}/reset`,
  )
  return data.values
}
