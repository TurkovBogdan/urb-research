import { defineStore } from 'pinia'
import { reactive, watch, computed } from 'vue'
import { i18n, setLocale, type AppLocale } from '@/plugins/i18n'
import { boolCodec, intCodec, persisted, strCodec, type Codec } from '@/shared/utils/persisted'
import { synced } from '@/shared/utils/synced'
import {
  DEFAULT_CODE_SIZE,
  DEFAULT_DIAGRAM_FONT,
  DEFAULT_HEADING_FONT,
  DEFAULT_HEADING_WEIGHT,
  DEFAULT_INTERFACE_FONT,
  DEFAULT_MONO_FONT,
  DEFAULT_READING_FONT,
  DEFAULT_READING_MEASURE,
  DEFAULT_READING_SIZE,
  DEFAULT_READING_WEIGHT,
  HEADING_FONTS,
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
// codec translates each to/from its localStorage string (see shared/utils/persisted).
//
// Здесь живут ВЫБОРЫ человека — то, что он однажды настроил под себя. Состояние интерфейсов
// (какой порядок в каком списке он оставил, пока работал) — соседний стор `ui-state`.
//
// Внешний вид приложения ведёт `synced`: источник истины — база (модуль `core_interface`),
// localStorage под ним остаётся кешем, который красит страницу до первого кадра. Имена ключей
// совпадают с ключами реестра на бэкенде. То, чего в реестре нет — таймзона, формат даты и
// наследие витрины, — остаётся на `persisted`, то есть живёт только в этом браузере.

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
    sidebarCollapsed: synced('interface_sidebar_collapsed', false, boolCodec),
    // Оглавление документа в боковой навигации деталки. У длинного тела это десяток-полтора
    // строк — кому они мешают, выключает их здесь, а сами разделы страницы остаются.
    documentNav: synced('interface_nav_document', true, boolCodec),
  })

  // Раскладка списков. Codec чинит значение на чтении, а не при показе: иначе испорченный ключ
  // разъезжался бы по всем потребителям, и каждому пришлось бы страховаться самому.
  const lists = reactive({
    researchView: synced<ResearchListView>('interface_list_research_view', DEFAULT_RESEARCH_LIST_VIEW, {
      parse: resolveResearchListView,
      serialize: (v) => v,
    }),
  })

  const message = reactive({
    mode: persisted('app.message.mode', 'text', strCodec), // 'html' | 'text'
    unsafe: persisted('app.message.unsafe', false, boolCodec), // true = safe view disabled (remote content shown)
  })

  const appearance = reactive({
    theme: synced<ThemeMode>('interface_theme', DEFAULT_THEME, strCodec as Codec<ThemeMode>),
  })

  // While the mode is `system` the OS can flip underneath us, so the scheme is re-applied on
  // the media-query event as well as on the choice itself.
  watch(() => appearance.theme, (mode) => applyScheme(resolveScheme(mode)), { immediate: true })
  onSystemSchemeChange((scheme) => {
    if (appearance.theme === 'system') applyScheme(scheme)
  })

  const typography = reactive({
    interfaceFont: synced('interface_font', DEFAULT_INTERFACE_FONT, strCodec),
    readingFont: synced('interface_font_reading', DEFAULT_READING_FONT, strCodec),
    headingFont: synced('interface_font_heading', DEFAULT_HEADING_FONT, strCodec),
    readingSize: synced('interface_font_reading_size', DEFAULT_READING_SIZE, intCodec),
    readingWeight: synced('interface_font_reading_weight', DEFAULT_READING_WEIGHT, intCodec),
    headingWeight: synced('interface_font_heading_weight', DEFAULT_HEADING_WEIGHT, intCodec),
    readingMeasure: synced('interface_font_reading_measure', DEFAULT_READING_MEASURE, intCodec),
    monoFont: synced('interface_font_mono', DEFAULT_MONO_FONT, strCodec),
    codeSize: synced('interface_font_code_size', DEFAULT_CODE_SIZE, intCodec),
  })

  // Оформление схем — свой узел, а не часть типографики: токенами оно не раздаётся, его читает
  // сам компонент схемы. Гарнитура тоже здесь, чтобы у настроек схем был один дом; в CSS она не
  // уходит — рендерер подставляет имя семьи внутрь SVG и по нему же считает ширину подписей.
  const diagrams = reactive({
    font: synced('interface_font_diagram', DEFAULT_DIAGRAM_FONT, strCodec),
    align: synced('interface_diagram_align', DEFAULT_DIAGRAM_ALIGN, strCodec as Codec<DiagramAlign>),
    maxHeight: synced('interface_diagram_max_height', DEFAULT_DIAGRAM_HEIGHT, intCodec),
  })

  watch(
    () => [
      typography.interfaceFont,
      typography.readingFont,
      typography.headingFont,
      typography.readingSize,
      typography.readingWeight,
      typography.headingWeight,
      typography.readingMeasure,
      typography.monoFont,
      typography.codeSize,
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
  headingFont: string
  readingSize: number
  readingWeight: number
  headingWeight: number
  readingMeasure: number
  monoFont: string
  codeSize: number
}

function applyTypographyTokens({ interfaceFont, readingFont, headingFont, readingSize, readingWeight, headingWeight, readingMeasure, monoFont, codeSize }: TypographyChoice): void {
  if (typeof document === 'undefined') return
  const root = document.documentElement.style
  const ui = fontStack(INTERFACE_FONTS, interfaceFont, DEFAULT_INTERFACE_FONT)
  root.setProperty('--font', ui)
  root.setProperty('--v-font-body', ui)
  root.setProperty('--v-font-heading', ui)
  root.setProperty('--font-reading', fontStack(READING_FONTS, readingFont, DEFAULT_READING_FONT))
  // Пункт «как шрифт текста» несёт стеком ссылку на соседний токен, поэтому развилки здесь нет:
  // при нём в `--font-heading` уезжает `var(--font-reading)` и следует за ним сам.
  root.setProperty('--font-heading', fontStack(HEADING_FONTS, headingFont, DEFAULT_HEADING_FONT))
  root.setProperty('--font-mono', fontStack(MONO_FONTS, monoFont, DEFAULT_MONO_FONT))
  // A stale or hand-edited storage value would otherwise reach CSS as `NaNpx` / `NaNch` and
  // take the whole prose scale — or the column width — down with it.
  const size = Number.isFinite(readingSize) ? readingSize : DEFAULT_READING_SIZE
  root.setProperty('--reading-size', `${size}px`)
  const weight = Number.isFinite(readingWeight) ? readingWeight : DEFAULT_READING_WEIGHT
  root.setProperty('--reading-weight', `${weight}`)
  const heading = Number.isFinite(headingWeight) ? headingWeight : DEFAULT_HEADING_WEIGHT
  root.setProperty('--heading-weight', `${heading}`)
  const measure = Number.isFinite(readingMeasure) ? readingMeasure : DEFAULT_READING_MEASURE
  root.setProperty('--reading-measure', measure === NO_MEASURE ? 'none' : `${measure}ch`)
  // Кегль листинга принадлежит зоне чтения, а не всякому блоку кода в приложении: сниппеты
  // дизайн-системы и панели подсказок живут своей жизнью. Зона чтения раздаёт его дальше сама
  // (`MarkdownRenderer` → `--code-size`), поэтому имя токена с приставкой роли.
  const code = Number.isFinite(codeSize) ? codeSize : DEFAULT_CODE_SIZE
  root.setProperty('--reading-code-size', `${code}px`)
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
