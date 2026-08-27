import { computed, type WritableComputedRef } from 'vue'
import { IconFileText } from '@tabler/icons-vue'

import type { SearchScope } from '@/components/SearchField.vue'

// Правило совпадения для глобального поиска по деталке исследования.
//
// Регистр не учитываем, пустой запрос совпадает со всем — так фильтр «выключен» не требует
// отдельной ветки у каждого потребителя.
export function normalizeQuery(query: string): string {
  return query.trim().toLowerCase()
}

export function matchesQuery(fields: (string | null | undefined)[], needle: string): boolean {
  if (!needle) return true
  return fields.some((field) => field && field.toLowerCase().includes(needle))
}

// Совпадает с `MIN_QUERY_LENGTH` службы глубокого поиска: по одной букве бэк читает все тела
// исследования ради мусорного ответа, поэтому клиент его и не зовёт.
export const MIN_DEEP_QUERY_LENGTH = 2

// ── Глубина поиска по реестру: одна переключаемая область у поля поиска ───────────────────────
//
// Область на обеих страницах одна и та же — «спуститься на слой ниже того, что страница
// показывает»: на странице групп это исследования полки, на странице полки — тексты исследований.
// Что лежит слоем ниже, знает страница (её подпись и подсказка), а бэк принимает булев параметр;
// `SearchField` же говорит набором включённых ключей, поэтому переходник живёт здесь.
const DEEPER_SCOPE = 'deeper'

export function deeperScope(label: string): SearchScope[] {
  return [{ key: DEEPER_SCOPE, icon: IconFileText, label }]
}

export function deeperScopeModel(
  enabled: () => boolean,
  toggle: (value: boolean) => void,
): WritableComputedRef<string[]> {
  return computed({
    get: () => (enabled() ? [DEEPER_SCOPE] : []),
    set: (keys) => toggle(keys.includes(DEEPER_SCOPE)),
  })
}
