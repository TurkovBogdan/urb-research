import { h } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { VDateInput } from 'vuetify/labs/VDateInput'
import { createVueI18nAdapter } from 'vuetify/locale/adapters/vue-i18n'
import { useI18n } from 'vue-i18n'
import 'vuetify/styles'
import { i18n } from './i18n'
import type { IconSet, IconProps } from 'vuetify'
import type { FunctionalComponent, SVGAttributes } from 'vue'
import {
  IconChevronUp, IconCheck, IconCircleX, IconX, IconCircleCheck,
  IconInfoCircle, IconAlertCircle, IconChevronLeft, IconChevronRight,
  IconSquareCheckFilled, IconSquare, IconSquareMinus, IconCircle,
  IconArrowUp, IconArrowDown, IconChevronDown, IconMenu2,
  IconCircleDot, IconPencil, IconStar, IconStarFilled, IconStarHalfFilled,
  IconRefresh, IconChevronsLeft, IconChevronsRight,
  IconSelector, IconPaperclip, IconPlus, IconMinus,
  IconCalendar, IconSquarePlus, IconDroplet,
} from '@tabler/icons-vue'

type TablerIcon = FunctionalComponent<SVGAttributes>

const tabler: IconSet = {
  component: (props: IconProps) => {
    const { icon } = props
    if (typeof icon !== 'string') return h(icon as TablerIcon)
    return h('span', { class: 'v-icon__unknown' }, String(icon))
  },
}

const tablerAliases: Record<string, TablerIcon> = {
  collapse:               IconChevronUp,
  complete:               IconCheck,
  cancel:                 IconCircleX,
  close:                  IconX,
  delete:                 IconCircleX,
  clear:                  IconCircleX,
  success:                IconCircleCheck,
  info:                   IconInfoCircle,
  warning:                IconAlertCircle,
  error:                  IconAlertCircle,
  prev:                   IconChevronLeft,
  next:                   IconChevronRight,
  checkboxOn:             IconSquareCheckFilled,
  checkboxOff:            IconSquare,
  checkboxIndeterminate:  IconSquareMinus,
  delimiter:              IconCircle,
  sortAsc:                IconArrowUp,
  sortDesc:               IconArrowDown,
  expand:                 IconChevronDown,
  menu:                   IconMenu2,
  subgroup:               IconChevronDown,
  dropdown:               IconChevronDown,
  radioOn:                IconCircleDot,
  radioOff:               IconCircle,
  edit:                   IconPencil,
  ratingEmpty:            IconStar,
  ratingFull:             IconStarFilled,
  ratingHalf:             IconStarHalfFilled,
  loading:                IconRefresh,
  first:                  IconChevronsLeft,
  last:                   IconChevronsRight,
  unfold:                 IconSelector,
  file:                   IconPaperclip,
  plus:                   IconPlus,
  minus:                  IconMinus,
  calendar:               IconCalendar,
  treeviewCollapse:       IconSquareMinus,
  treeviewExpand:         IconSquarePlus,
  eyeDropper:             IconDroplet,
}

export default createVuetify({
  components: { ...components, VDateInput },
  directives,
  // Vuetify component strings follow the active vue-i18n locale (reads `$vuetify.*`).
  // Cast: the adapter expects a loosely-typed I18n<any>; our instance is narrowed
  // to the literal message tree, which is structurally compatible at runtime.
  locale: { adapter: createVueI18nAdapter({ i18n: i18n as never, useI18n }) },
  // Mobile chrome (overlay drawer + top app-bar) kicks in below `md` (<960px) —
  // same threshold as PageHeader's responsive reflow (max-width: 959px).
  display: { mobileBreakpoint: 'md' },
  icons: {
    defaultSet: 'tabler',
    aliases: tablerAliases,
    sets: { tabler },
  },

  // Дефолтные пропы — убирают нужду писать их везде в шаблонах
  defaults: {
    VTextField:    { variant: 'outlined' },
    // Мультиселекты по умолчанию рендерят выбранное чипами в нашем стиле
    // (.v-select--multiple .v-chip в main.scss); closableChips даёт ×-удаление
    // прямо в поле. Vuetify включает чипы и для одиночного выбора — там CSS
    // возвращает им вид простого текста (.v-select--single .v-chip в main.scss).
    VSelect:       { variant: 'outlined', chips: true, closableChips: true },
    VAutocomplete: { variant: 'outlined', chips: true, closableChips: true },
    VCombobox:     { variant: 'outlined', chips: true, closableChips: true },
    VTextarea:     { variant: 'outlined' },
    VNumberInput:  { variant: 'outlined' },
    VCheckbox:     { color: 'primary' },
    VSwitch:       { color: 'primary', inset: true },
    VRadio:        { color: 'primary' },
    VSlider:       { color: 'primary' },
    VRangeSlider:  { color: 'primary' },
    VDivider:      { color: 'outline' },
    VBtn:          { variant: 'flat', elevation: 0 },
    // Кликабельная карточка по умолчанию плоская, без ripple — Material-волна
    // не вписывается в flat-язык (подсветка идёт обводкой, см. .v-card--link в main.scss).
    VCard:         { ripple: false },
    VBtnGroup:     { variant: 'outlined', divided: true, elevation: 0 },
    VBtnToggle:    { variant: 'outlined', divided: true, elevation: 0 },
    VDateInput:    { variant: 'outlined', hideDetails: true, color: 'primary' },
    VDatePicker:   { color: 'primary', showAdjacentMonths: true },
    VTimePicker:   { color: 'primary', format: '24hr' },
    VPagination:       { activeColor: 'primary' },
    VProgressCircular: { color: 'primary' },
    VProgressLinear:   { color: 'primary' },
  },

  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        // Vuetify парсит цвета как hex для построения rgba-оверлеев — oklch() даёт warn.
        // Значения соответствуют токенам в styles/main.scss.
        colors: {
          background:           '#0F1115',  // --bg
          surface:              '#1A1E26',  // --surface
          'surface-variant':    '#15181E',  // --sidebar-bg / panel
          'surface-bright':     '#232833',  // --surface-hi
          'on-background':      '#E6E9EF',  // --text
          'on-surface':         '#E6E9EF',
          'on-surface-variant': '#E6E9EF',
          primary:              '#3B9EFF',  // --accent
          'primary-darken-1':   '#2C6FB0',  // --accent-mid
          secondary:            '#9AA3B2',  // --text-muted
          error:                '#FF5A5D',  // --error
          success:              '#4ECB71',  // --success (green)
          warning:              '#F0A93D',  // --warn
          info:                 '#3B9EFF',  // --info
          outline:              '#2A2F3A',  // --border
        },
        variables: {
          // Прозрачности — Vuetify использует их в rgba() для оверлеев и текста
          'high-emphasis-opacity':   1,
          'medium-emphasis-opacity': 0.6,
          'disabled-opacity':        0.38,
          'border-opacity':          1,
          'hover-opacity':           0.04,
          'focus-opacity':           0.08,
          'selected-opacity':        0.06,
          'activated-opacity':       0.08,
          'pressed-opacity':         0.08,
        },
      },
    },
  },
})
