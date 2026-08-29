import { computed, type WritableComputedRef } from 'vue'
import { IconFileText, IconNotes, IconWorldSearch } from '@tabler/icons-vue'

import type { SearchScope } from '@/components/SearchField.vue'

import type { SearchScopes } from './stores/researches.store'

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

// ── Слои поиска по реестру: три переключаемые области у одного поля ───────────────────────────
//
// Реестр в отличие от полки показывает ВСЕ исследования, поэтому и стог у него набирается
// слоями, а не одной глубиной: тело исследования, написанное внутри него (зоны с брифом и
// заметки) и материал источников. Название с описанием в стоге всегда — ими исследование
// названо в списке, и выключаемая основа означала бы поиск, не находящий искомое по имени.
//
// Ключи совпадают с флагами стора один в один, поэтому переходник между набором `SearchField`
// и тремя булевыми полями сводится к перечислению — и живёт здесь, рядом с самими областями.
export const SCOPE_BODY = 'body'
export const SCOPE_AREAS_AND_NOTES = 'areas_and_notes'
export const SCOPE_SOURCES = 'sources'

const SCOPE_ICONS = {
  [SCOPE_BODY]: IconFileText,
  [SCOPE_AREAS_AND_NOTES]: IconNotes,
  [SCOPE_SOURCES]: IconWorldSearch,
}

/** Набор областей поля; подписи даёт страница — словарь живёт у фичи, а не в этом переходнике. */
export function registryScopes(label: (scope: string) => string): SearchScope[] {
  return Object.entries(SCOPE_ICONS).map(([key, icon]) => ({ key, icon, label: label(key) }))
}

export function registryScopesModel(
  scopes: () => SearchScopes,
  apply: (next: SearchScopes) => void,
): WritableComputedRef<string[]> {
  return computed({
    get: () => {
      const { inBody, inAreasAndNotes, inSources } = scopes()
      return [
        ...(inBody ? [SCOPE_BODY] : []),
        ...(inAreasAndNotes ? [SCOPE_AREAS_AND_NOTES] : []),
        ...(inSources ? [SCOPE_SOURCES] : []),
      ]
    },
    set: (keys) =>
      apply({
        inBody: keys.includes(SCOPE_BODY),
        inAreasAndNotes: keys.includes(SCOPE_AREAS_AND_NOTES),
        inSources: keys.includes(SCOPE_SOURCES),
      }),
  })
}
