import { defineStore } from 'pinia'
import { ref, reactive, watch, computed, type Ref } from 'vue'
import { i18n, setLocale, type AppLocale } from '@/plugins/i18n'
import {
  DEFAULT_DIAGRAM_FONT,
  DEFAULT_INTERFACE_FONT,
  DEFAULT_MONO_FONT,
  DEFAULT_READING_FONT,
  DEFAULT_READING_MEASURE,
  DEFAULT_READING_SIZE,
  INTERFACE_FONTS,
  MONO_FONTS,
  NO_MEASURE,
  READING_FONTS,
  fontStack,
} from '@/constants/fonts'
import {
  DEFAULT_DIAGRAM_ALIGN,
  DEFAULT_DIAGRAM_HEIGHT,
  type DiagramAlign,
} from '@/constants/diagrams'
import {
  DEFAULT_RESEARCH_LIST_VIEW,
  resolveResearchListView,
  type ResearchListView,
} from '@/constants/lists'
import {
  DEFAULT_THEME,
  onSystemSchemeChange,
  resolveScheme,
  type ColorScheme,
  type ThemeMode,
} from '@/constants/theme'
import vuetify from '@/plugins/vuetify'

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
const intCodec: Codec<number> = { parse: (raw) => Number.parseInt(raw, 10), serialize: (v) => String(v) }

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
    // Оглавление документа в боковой навигации деталки. У длинного тела это десяток-полтора
    // строк — кому они мешают, выключает их здесь, а сами разделы страницы остаются.
    documentNav: persisted('app.nav.document', true, boolCodec),
  })

  // Раскладка списков. Codec чинит значение на чтении, а не при показе: иначе испорченный ключ
  // разъезжался бы по всем потребителям, и каждому пришлось бы страховаться самому.
  const lists = reactive({
    researchView: persisted<ResearchListView>('app.list.research_view', DEFAULT_RESEARCH_LIST_VIEW, {
      parse: resolveResearchListView,
      serialize: (v) => v,
    }),
  })

  const message = reactive({
    mode: persisted('app.message.mode', 'text', strCodec), // 'html' | 'text'
    unsafe: persisted('app.message.unsafe', false, boolCodec), // true = safe view disabled (remote content shown)
  })

  const appearance = reactive({
    theme: persisted<ThemeMode>('app.theme', DEFAULT_THEME, strCodec as Codec<ThemeMode>),
  })

  // While the mode is `system` the OS can flip underneath us, so the scheme is re-applied on
  // the media-query event as well as on the choice itself.
  watch(() => appearance.theme, (mode) => applyScheme(resolveScheme(mode)), { immediate: true })
  onSystemSchemeChange((scheme) => {
    if (appearance.theme === 'system') applyScheme(scheme)
  })

  const typography = reactive({
    interfaceFont: persisted('app.font.interface', DEFAULT_INTERFACE_FONT, strCodec),
    readingFont: persisted('app.font.reading', DEFAULT_READING_FONT, strCodec),
    readingSize: persisted('app.font.reading_size', DEFAULT_READING_SIZE, intCodec),
    readingMeasure: persisted('app.font.reading_measure', DEFAULT_READING_MEASURE, intCodec),
    monoFont: persisted('app.font.mono', DEFAULT_MONO_FONT, strCodec),
  })

  // Оформление схем — свой узел, а не часть типографики: токенами оно не раздаётся, его читает
  // сам компонент схемы. Гарнитура тоже здесь, чтобы у настроек схем был один дом; в CSS она не
  // уходит — рендерер подставляет имя семьи внутрь SVG и по нему же считает ширину подписей.
  const diagrams = reactive({
    font: persisted('app.font.diagram', DEFAULT_DIAGRAM_FONT, strCodec),
    align: persisted('app.diagram.align', DEFAULT_DIAGRAM_ALIGN, strCodec as Codec<DiagramAlign>),
    maxHeight: persisted('app.diagram.max_height', DEFAULT_DIAGRAM_HEIGHT, intCodec),
  })

  watch(
    () => [
      typography.interfaceFont,
      typography.readingFont,
      typography.readingSize,
      typography.readingMeasure,
      typography.monoFont,
    ],
    () => applyTypographyTokens(typography),
    { immediate: true },
  )

  return { locale, ui, lists, message, appearance, typography, diagrams }
})

// Two consumers, one name: the attribute drives the CSS token palettes (styles/main.scss),
// which is what the app itself is painted from, and Vuetify is told separately because it
// colours its own components from its theme map rather than from the tokens.
function applyScheme(scheme: ColorScheme): void {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.theme = scheme
  vuetify.theme.change(scheme)
}

// The choices reach CSS as tokens on <html>, which outrank the `:root` defaults in main.scss.
// Vuetify's own `--v-font-*` are set alongside `--font`: its typography roles read those, and
// left unset they keep rendering the framework default (Roboto) wherever a component style
// wins the cascade.
interface TypographyChoice {
  interfaceFont: string
  readingFont: string
  readingSize: number
  readingMeasure: number
  monoFont: string
}

function applyTypographyTokens({ interfaceFont, readingFont, readingSize, readingMeasure, monoFont }: TypographyChoice): void {
  if (typeof document === 'undefined') return
  const root = document.documentElement.style
  const ui = fontStack(INTERFACE_FONTS, interfaceFont, DEFAULT_INTERFACE_FONT)
  root.setProperty('--font', ui)
  root.setProperty('--v-font-body', ui)
  root.setProperty('--v-font-heading', ui)
  root.setProperty('--font-reading', fontStack(READING_FONTS, readingFont, DEFAULT_READING_FONT))
  root.setProperty('--font-mono', fontStack(MONO_FONTS, monoFont, DEFAULT_MONO_FONT))
  // A stale or hand-edited storage value would otherwise reach CSS as `NaNpx` / `NaNch` and
  // take the whole prose scale — or the column width — down with it.
  const size = Number.isFinite(readingSize) ? readingSize : DEFAULT_READING_SIZE
  root.setProperty('--reading-size', `${size}px`)
  const measure = Number.isFinite(readingMeasure) ? readingMeasure : DEFAULT_READING_MEASURE
  root.setProperty('--reading-measure', measure === NO_MEASURE ? 'none' : `${measure}ch`)
}

// IANA zone list for the picker; empty if the engine lacks Intl.supportedValuesOf.
export function timezoneOptions(): string[] {
  const intl = Intl as unknown as { supportedValuesOf?: (key: string) => string[] }
  try {
    return intl.supportedValuesOf ? intl.supportedValuesOf('timeZone') : []
  } catch {
    return []
  }
}
