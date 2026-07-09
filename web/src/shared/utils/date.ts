import { DateTime } from 'luxon'

import { i18n } from '@/plugins/i18n'
import { AUTO, useSettingsStore } from '@/stores/settings'

// All formatters follow the app's active locale (plugins/i18n.ts → setLocale) plus
// two user preferences (stores/settings.ts → locale.timezone / locale.dateFormat),
// each defaulting to "auto" (locale-derived format / browser zone). Reading the store
// inside each formatter makes every rendered date re-render when a preference changes.
function _locale(): string {
  return i18n.global.locale.value
}

function _t(key: string, named?: Record<string, unknown>): string {
  return i18n.global.t(key, named ?? {})
}

// Date part: user-picked Luxon token, or — when "auto" — locale-specific separator
// (ru "dd.MM.yyyy", en "dd/MM/yyyy"). Time-only formats are identical across locales (24h).
function _datePart(): string {
  const { locale } = useSettingsStore()
  if (locale.dateFormat !== AUTO) return locale.dateFormat
  return _locale() === 'en' ? 'dd/MM/yyyy' : 'dd.MM.yyyy'
}

// Apply the display timezone: browser-local for "auto", else the picked IANA zone
// (falling back to local if the stored zone is somehow invalid).
function _zoned(dt: DateTime): DateTime {
  const { locale } = useSettingsStore()
  if (locale.timezone === AUTO) return dt.toLocal()
  const z = dt.setZone(locale.timezone)
  return z.isValid ? z : dt.toLocal()
}

function _parse(s: string | null): DateTime | null {
  if (!s) return null
  return _zoned(DateTime.fromSQL(s, { zone: 'utc' }))
}

/** ru "dd.MM.yyyy" / en "dd/MM/yyyy" */
export function fmtDate(s: string | null): string {
  return _parse(s)?.toFormat(_datePart()) ?? '—'
}

/** Date-only, kept in UTC with no local shift — for day-aligned bounds. ru "dd.MM.yyyy" / en "dd/MM/yyyy" */
export function fmtDateUtc(s: string | null): string {
  if (!s) return '—'
  return DateTime.fromSQL(s, { zone: 'utc' }).toFormat(_datePart())
}

/** Zoned calendar-day key (yyyy-MM-dd) — sortable, for grouping rows by day. */
export function dayKey(s: string | null): string | null {
  return _parse(s)?.toFormat('yyyy-MM-dd') ?? null
}

/** Localized weekday name, capitalized: "Пятница" / "Friday". */
export function fmtWeekday(s: string | null): string {
  const dt = _parse(s)
  if (!dt) return ''
  const wd = dt.toFormat('cccc', { locale: _locale() })
  return wd.charAt(0).toUpperCase() + wd.slice(1)
}

/** date + " HH:mm" */
export function fmtDateTime(s: string | null): string {
  return _parse(s)?.toFormat(`${_datePart()} HH:mm`) ?? '—'
}

/** date + " HH:mm:ss" */
export function fmtDateTimeSec(s: string | null): string {
  return _parse(s)?.toFormat(`${_datePart()} HH:mm:ss`) ?? '—'
}

/** HH:mm */
export function fmtTime(s: string | null): string {
  return _parse(s)?.toFormat('HH:mm') ?? '—'
}

/** HH:mm:ss.SSS */
export function fmtTimeSec(s: string | null): string {
  return _parse(s)?.toFormat('HH:mm:ss.SSS') ?? '—'
}

const JUST_NOW_THRESHOLD_SECONDS = 30

/** Relative in the active locale: "5 минут назад" / "5 minutes ago"; within ±30s → "только что" / "just now" */
export function fmtRelative(s: string | null): string {
  const dt = _parse(s)
  if (!dt) return ''
  if (Math.abs(dt.diffNow('seconds').seconds) <= JUST_NOW_THRESHOLD_SECONDS) return _t('common.date.just_now')
  return dt.toRelative({ locale: _locale() }) ?? ''
}

/** Relative magnitude only, no "ago"/"in" affix: "5 минут" / "5 minutes" */
export function fmtRelativeShort(s: string | null): string {
  const dt = _parse(s)
  if (!dt) return ''
  const rel = dt.toRelative({ locale: _locale() })
  if (!rel) return ''
  // Strip ru ("через …"/"… назад") and en ("in …"/"… ago") affixes.
  return rel
    .replace(/^(через|in)\s+/i, '')
    .replace(/\s+(назад|ago)$/i, '')
}

/** Whole-day delta: "сегодня" / "вчера" / "5 дн. назад" / "через 3 дн." */
export function fmtDaysAgo(s: string | null): string {
  const dt = _parse(s)
  if (!dt) return ''
  const days = Math.floor(DateTime.now().diff(dt, 'days').days)
  if (days < 0) return _t('common.date.in_days', { n: -days })
  if (days === 0) return _t('common.date.today')
  if (days === 1) return _t('common.date.yesterday')
  return _t('common.date.days_ago', { n: days })
}

/** Duration between two UTC strings */
export function fmtDuration(startedAt: string, finishedAt: string | null): string {
  if (!finishedAt) return '—'
  const ms = DateTime.fromSQL(finishedAt, { zone: 'utc' }).toMillis()
    - DateTime.fromSQL(startedAt, { zone: 'utc' }).toMillis()
  if (ms < 1000) return `${ms} ms`
  const sec = Math.round(ms / 1000)
  if (sec < 60) return `${sec} s`
  const min = Math.floor(sec / 60)
  return `${min}m ${sec % 60}s`
}
