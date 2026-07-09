import type { PageStatus, QueryStatus } from './api'

type BadgeColor = 'accent' | 'success' | 'error' | 'warn' | 'muted'

// Статус → цвет StatusBadge. Текст статуса берётся из i18n (web_search.*.status.*).
export const QUERY_STATUS_COLOR: Record<QueryStatus, BadgeColor> = {
  pending: 'muted',
  processing: 'accent',
  done: 'success',
  error: 'error',
}

export const PAGE_STATUS_COLOR: Record<PageStatus, BadgeColor> = {
  pending: 'muted',
  processing: 'accent',
  done: 'success',
  error: 'error',
}

export const QUERY_STATUSES: QueryStatus[] = ['pending', 'processing', 'done', 'error']
export const PAGE_STATUSES: PageStatus[] = ['pending', 'processing', 'done', 'error']

export const SEARCH_PROVIDERS = ['tavily', 'firecrawl', 'xai'] as const
