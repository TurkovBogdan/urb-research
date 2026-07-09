import { defineStore } from 'pinia'
import { ref, reactive, watch, computed, type Ref } from 'vue'
import { i18n, setLocale, type AppLocale } from '@/plugins/i18n'

// Central store for the user's local (client-side) settings — the single home for
// everything that used to live scattered across plugins/preferences.ts, layout/store.ts
// and plugins/i18n.ts. State holds NORMAL typed values (real booleans / enums); the
// codec translates each to/from its localStorage string. A value equal to its default is
// NOT written (the key is removed), so storage holds only deliberate deviations.

interface Codec<T> {
  parse: (raw: string) => T
  serialize: (value: T) => string
}

const boolCodec: Codec<boolean> = { parse: (raw) => raw === '1', serialize: (v) => (v ? '1' : '0') }
const strCodec: Codec<string> = { parse: (raw) => raw, serialize: (v) => v }

function persisted<T>(key: string, def: T, codec: Codec<T>): Ref<T> {
  const has = typeof localStorage !== 'undefined'
  const raw = has ? localStorage.getItem(key) : null
  const state = ref(raw === null ? def : codec.parse(raw)) as Ref<T>
  watch(state, (v) => {
    if (!has) return
    if (v === def) localStorage.removeItem(key)
    else localStorage.setItem(key, codec.serialize(v))
  })
  return state
}

export const AUTO = 'auto'

// Selectable date formats as Luxon tokens. "auto" is handled separately (locale-derived).
export const DATE_FORMATS = ['dd.MM.yyyy', 'dd/MM/yyyy', 'yyyy-MM-dd', 'MM/dd/yyyy'] as const

export const useSettingsStore = defineStore('settings', () => {
  // `reactive` unwraps the nested refs/computed, so `settings.locale.timezone` reads the
  // plain value and `settings.message.unsafe` reads a real boolean — while each underlying
  // ref keeps its own persistence watcher.
  const locale = reactive({
    // language is a façade over i18n (it bootstraps before Pinia and owns the
    // `app.locale` key); the setter routes through setLocale so Vuetify follows.
    language: computed<AppLocale>({
      get: () => i18n.global.locale.value as AppLocale,
      set: (v) => setLocale(v),
    }),
    timezone: persisted('app.timezone', AUTO, strCodec),
    dateFormat: persisted('app.date_format', AUTO, strCodec),
  })

  const ui = reactive({
    sidebarCollapsed: persisted('app.sidebar_collapsed', false, boolCodec),
  })

  const message = reactive({
    mode: persisted('app.message.mode', 'text', strCodec), // 'html' | 'text'
    unsafe: persisted('app.message.unsafe', false, boolCodec), // true = safe view disabled (remote content shown)
  })

  return { locale, ui, message }
})

// IANA zone list for the picker; empty if the engine lacks Intl.supportedValuesOf.
export function timezoneOptions(): string[] {
  const intl = Intl as unknown as { supportedValuesOf?: (key: string) => string[] }
  try {
    return intl.supportedValuesOf ? intl.supportedValuesOf('timeZone') : []
  } catch {
    return []
  }
}
