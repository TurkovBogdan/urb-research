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
