// Font families offered in interface settings, in two independent roles.
//
// The split is the point: interface text is scanned in small sizes (table rows, list
// items, labels) while a research body is read continuously, and the two roles want
// different families as well as different sizes. The chosen stacks reach CSS as the
// `--font` and `--font-reading` tokens (see stores/settings.ts).
//
// A bundled family must have a matching @font-face in styles/fonts.scss; the system
// entries deliberately have none — they resolve to whatever the OS provides.

export interface FontOption {
  code: string
  label: string
  // The complete CSS font-family value, fallbacks included.
  stack: string
  // Shown under the option as the reason to pick it.
  note: string
}

const SANS_FALLBACK = 'system-ui, -apple-system, "Segoe UI", sans-serif'
const SERIF_FALLBACK = 'Georgia, "Times New Roman", serif'
const MONO_FALLBACK = 'ui-monospace, SFMono-Regular, Consolas, monospace'

const ONEST: FontOption = {
  code: 'onest',
  label: 'Onest',
  stack: `'Onest', ${SANS_FALLBACK}`,
  note: 'Гротеск с кириллицей в основе. Шрифт приложения по умолчанию.',
}

const INTER: FontOption = {
  code: 'inter',
  label: 'Inter',
  stack: `'Inter', ${SANS_FALLBACK}`,
  note: 'Спроектирован под плотные интерфейсы: крупные строчные, узкие пропорции.',
}

const GOLOS: FontOption = {
  code: 'golos',
  label: 'Golos Text',
  stack: `'Golos Text', ${SANS_FALLBACK}`,
  note: 'Нарисован под чтение русского текста, а не под интерфейс.',
}

const LITERATA: FontOption = {
  code: 'literata',
  label: 'Literata',
  stack: `'Literata', ${SERIF_FALLBACK}`,
  note: 'Экранная антиква для длинного чтения (шрифт Google Play Books).',
}

const JETBRAINS_MONO: FontOption = {
  code: 'jetbrains-mono',
  label: 'JetBrains Mono',
  stack: `'JetBrains Mono', ${MONO_FALLBACK}`,
  note: 'Нарисован под чтение кода: широкие пробелы, различимые ноль и буква O.',
}

const SYSTEM_MONO: FontOption = {
  code: 'system-mono',
  label: 'Системный моноширинный',
  stack: MONO_FALLBACK,
  note: 'Consolas, Menlo или их замена из системы — ничего не загружается.',
}

const SYSTEM_SANS: FontOption = {
  code: 'system',
  label: 'Системный гротеск',
  stack: SANS_FALLBACK,
  note: 'Шрифт операционной системы — ничего не загружается.',
}

const SYSTEM_SERIF: FontOption = {
  code: 'system-serif',
  label: 'Системная антиква',
  stack: SERIF_FALLBACK,
  note: 'Georgia или её замена из системы — ничего не загружается.',
}

export const INTERFACE_FONTS: FontOption[] = [ONEST, INTER, GOLOS, SYSTEM_SANS]

export const READING_FONTS: FontOption[] = [ONEST, GOLOS, LITERATA, INTER, SYSTEM_SERIF, SYSTEM_SANS]

// Код — своя роль: моноширинный набор в блоках кода, инлайновых чипах и технических подписях
// (`--font-mono`). Схемам он не предлагается: раскладка меряет подписи буквенными пропорциями,
// а моноширинная строка шире — она вылезла бы за границы блоков.
export const MONO_FONTS: FontOption[] = [JETBRAINS_MONO, SYSTEM_MONO]

// Схемы — третья роль: подпись внутри блока живёт в тесной коробке, ширину которой раскладка
// посчитала заранее по метрикам Inter. Отсюда и состав, и порядок: антиквы в списке нет, а
// Inter стоит по умолчанию — на нём подписи ложатся в коробки точнее всего.
export const DIAGRAM_FONTS: FontOption[] = [INTER, ONEST, GOLOS, SYSTEM_SANS]

export const DEFAULT_INTERFACE_FONT = ONEST.code
export const DEFAULT_READING_FONT = ONEST.code
export const DEFAULT_MONO_FONT = JETBRAINS_MONO.code
export const DEFAULT_DIAGRAM_FONT = INTER.code

// Base size of the reading zone in pixels. Everything inside a body is sized in `em` off
// this one value, so a step moves the whole prose scale — headings, code, tables, indents —
// and not just the paragraphs. The floor is the lower bound for continuous reading; the
// ceiling is where a line stops fitting the column on a laptop screen.
export const READING_SIZES = [14, 15, 16, 17, 18, 20] as const

export const DEFAULT_READING_SIZE = 14

// Width of the running-text column, in `ch`. Tables, code blocks and images are outside it —
// they are scanned rather than read line by line, and squeezing them into the text column only
// makes them scroll. `0` means no cap at all: the text runs to the full width of the panel.
//
// A caveat that makes the numbers read low: `ch` is the width of the digit zero, which runs
// wider than an average Cyrillic lowercase letter, so a line holds roughly a fifth more
// characters than the number suggests.
export const READING_MEASURES = [64, 76, 92, 108, 124, 0] as const

export const DEFAULT_READING_MEASURE = 92

export const NO_MEASURE = 0

// An unknown code (a stale localStorage value, a family dropped from the list) falls
// back to the role's default rather than leaving the token empty.
export function fontStack(options: FontOption[], code: string, fallback: string): string {
  const chosen = options.find((option) => option.code === code)
    ?? options.find((option) => option.code === fallback)
  return chosen?.stack ?? SANS_FALLBACK
}

// Рендереру схем нужно имя гарнитуры, а не стек: он подставляет его в собственное правило
// внутри SVG и дописывает запасные варианты сам. Отсюда и первая семья стека вместо него целиком.
export function fontFamilyName(options: FontOption[], code: string, fallback: string): string {
  return fontStack(options, code, fallback).split(',')[0].replace(/['"]/g, '').trim()
}
