import type { NoteKind, SourceStatus } from './api'

type BadgeColor = 'accent' | 'success' | 'error' | 'warn' | 'muted'

// Статус источника → цвет StatusBadge. Текст — i18n (research.source.status.*).
export const SOURCE_STATUS_COLOR: Record<SourceStatus, BadgeColor> = {
  pending: 'warn',
  kept: 'success',
  filtered: 'muted',
  fetch_error: 'error',
}

// Тип заметки → цвет StatusBadge. Текст — i18n (research.note.kind.*).
export const NOTE_KIND_COLOR: Record<NoteKind, BadgeColor> = {
  result: 'success',
  idea: 'accent',
  question: 'warn',
  memory: 'muted',
  decision: 'accent',
  clarification: 'muted',
}
