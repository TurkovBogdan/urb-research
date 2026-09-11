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

const GOLOS: FontOption = {
  code: 'golos',
  label: 'Golos Text',
  stack: `'Golos Text', ${SANS_FALLBACK}`,
  note: 'Нарисован под чтение русского текста, а не под интерфейс. Курсива в семействе нет.',
}

const IBM_PLEX_SANS: FontOption = {
  code: 'ibm-plex-sans',
  label: 'IBM Plex Sans',
  stack: `'IBM Plex Sans', ${SANS_FALLBACK}`,
  note: 'Кириллицу рисовала Александра Самуленкова. Единственный здесь с болгарскими начертаниями.',
}

const PT_SANS: FontOption = {
  code: 'pt-sans',
  label: 'PT Sans',
  stack: `'PT Sans', ${SANS_FALLBACK}`,
  note: 'Сделан под языки России: самое широкое покрытие кириллицы и настоящий курсив.',
}

const COMMISSIONER: FontOption = {
  code: 'commissioner',
  label: 'Commissioner',
  stack: `'Commissioner', ${SANS_FALLBACK}`,
  note: 'Гуманистический гротеск, кириллицу консультировала Мария Дореули.',
}

const GEOLOGICA: FontOption = {
  code: 'geologica',
  label: 'Geologica',
  stack: `'Geologica', ${SANS_FALLBACK}`,
  note: 'Широкие пропорции и открытые апертуры — то, что помогает слабовидящим читателям.',
}

const LITERATA: FontOption = {
  code: 'literata',
  label: 'Literata',
  stack: `'Literata', ${SERIF_FALLBACK}`,
  note: 'Экранная антиква для длинного чтения (шрифт Google Play Books).',
}

const PT_SERIF: FontOption = {
  code: 'pt-serif',
  label: 'PT Serif',
  stack: `'PT Serif', ${SERIF_FALLBACK}`,
  note: 'Антиква той же семьи, что PT Sans; её кириллицу эксперты считают ещё удачнее.',
}

const SOURCE_SERIF: FontOption = {
  code: 'source-serif',
  label: 'Source Serif',
  stack: `'Source Serif', ${SERIF_FALLBACK}`,
  note: 'Экранная антиква с оптической осью; кириллица лучше, чем у парного Source Sans.',
}

const LORA: FontOption = {
  code: 'lora',
  label: 'Lora',
  stack: `'Lora', ${SERIF_FALLBACK}`,
  note: 'Каллиграфическая антиква; самый широкий набор локализованных начертаний кириллицы.',
}

const PIAZZOLLA: FontOption = {
  code: 'piazzolla',
  label: 'Piazzolla',
  stack: `'Piazzolla', ${SERIF_FALLBACK}`,
  note: 'Оптическая ось 8–30 pt: рисунок знака подстраивается под кегль набора.',
}

const SPECTRAL: FontOption = {
  code: 'spectral',
  label: 'Spectral',
  stack: `'Spectral', ${SERIF_FALLBACK}`,
  note: 'Антиква Google Docs; кириллицу рисовали Илья Рудерман и Юрий Остроменцкий.',
}

const JETBRAINS_MONO: FontOption = {
  code: 'jetbrains-mono',
  label: 'JetBrains Mono',
  stack: `'JetBrains Mono', ${MONO_FALLBACK}`,
  note: 'Нарисован под чтение кода: широкие пробелы, различимые ноль и буква O.',
}

const IBM_PLEX_MONO: FontOption = {
  code: 'ibm-plex-mono',
  label: 'IBM Plex Mono',
  stack: `'IBM Plex Mono', ${MONO_FALLBACK}`,
  note: 'Моноширинная пара к IBM Plex Sans — если интерфейс набран им же.',
}

const MARTIAN_MONO: FontOption = {
  code: 'martian-mono',
  label: 'Martian Mono',
  stack: `'Martian Mono', ${MONO_FALLBACK}`,
  note: 'Единственный моноширинный с осью ширины. Сербских и македонских букв в нём нет.',
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

export const INTERFACE_FONTS: FontOption[] = [
  ONEST,
  GOLOS,
  IBM_PLEX_SANS,
  PT_SANS,
  COMMISSIONER,
  GEOLOGICA,
  SYSTEM_SANS,
]

// Антиквы стоят первыми: роль чтения — это длинный текст, и именно здесь засечки уместны.
export const READING_FONTS: FontOption[] = [
  LITERATA,
  PT_SERIF,
  SOURCE_SERIF,
  LORA,
  PIAZZOLLA,
  SPECTRAL,
  ONEST,
  GOLOS,
  IBM_PLEX_SANS,
  PT_SANS,
  SYSTEM_SERIF,
  SYSTEM_SANS,
]

// «Как шрифт текста» — не гарнитура, а отказ от выбора: заголовки набираются тем же, чем набран
// текст, и следуют за ним при смене. Стек — ссылка на его токен, поэтому строка списка набрана
// тем, что выбрано сейчас, а в CSS значение подставляется без развилки в коде.
const HEADING_AS_READING: FontOption = {
  code: 'reading',
  label: 'Как шрифт текста',
  stack: 'var(--font-reading)',
  note: 'Заголовки набраны тем же, чем текст, и меняются вместе с ним.',
}

// Заголовки берут либо шрифт текста, либо свой — набор тот же, что у зоны чтения: заголовок
// живёт в том же документе, и семьи, негодные для чтения подряд, негодны и здесь.
export const HEADING_FONTS: FontOption[] = [HEADING_AS_READING, ...READING_FONTS]

// Код — своя роль: моноширинный набор в блоках кода, инлайновых чипах и технических подписях
// (`--font-mono`). Схемам он не предлагается: раскладка меряет подписи буквенными пропорциями,
// а моноширинная строка шире — она вылезла бы за границы блоков.
export const MONO_FONTS: FontOption[] = [JETBRAINS_MONO, IBM_PLEX_MONO, MARTIAN_MONO, SYSTEM_MONO]

// Схемы — третья роль: подпись внутри блока живёт в тесной коробке, и рендерер меряет её
// той гарнитурой, что выбрана. Отсюда состав: только гротески с плотным рисунком — антиква
// и моноширинный набирают подпись шире, чем рассчитана коробка.
export const DIAGRAM_FONTS: FontOption[] = [ONEST, GOLOS, IBM_PLEX_SANS, PT_SANS, SYSTEM_SANS]

export const DEFAULT_INTERFACE_FONT = ONEST.code
export const DEFAULT_READING_FONT = ONEST.code
export const DEFAULT_HEADING_FONT = HEADING_AS_READING.code
export const DEFAULT_MONO_FONT = JETBRAINS_MONO.code
export const DEFAULT_DIAGRAM_FONT = ONEST.code

// Base size of the reading zone in pixels. Everything inside a body is sized in `em` off
// this one value, so a step moves the whole prose scale — headings, code, tables, indents —
// and not just the paragraphs. The floor is the lower bound for continuous reading; the
// ceiling is where a line stops fitting the column on a laptop screen.
export const READING_SIZES = [14, 15, 16, 17, 18, 20] as const

export const DEFAULT_READING_SIZE = 14

// Насыщенность зоны чтения — вся шкала CSS, от 100 до 900. Заголовки и выделения в теле
// не следуют за ней: они заданы своим весом, иначе разница между текстом и выделением в нём
// исчезла бы вместе с выбором.
//
// Оговорка про нижний край: начертания легче нормального есть не у всех подключённых семей
// (у PT Sans, PT Serif, Spectral и IBM Plex Mono их нет вовсе, у Golos Text ось начинается
// с 400) — там браузер возьмёт ближайшее доступное, и 100–300 нарисуются как 400.
export const READING_WEIGHTS = [100, 200, 300, 400, 500, 600, 700, 800, 900] as const

export const DEFAULT_READING_WEIGHT = 300

// Заголовки идут по той же шкале, но своим выбором: разница между ними и текстом — это и есть
// то, чем читается разбиение на разделы, и держать её приходится в паре с весом текста.
export const DEFAULT_HEADING_WEIGHT = 600

// Кегль блока кода в теле документа, в пикселях. Своя лестница и свой выбор: моноширинный набор
// при том же кегле выглядит крупнее пропорционального, и листинг, набранный вровень с текстом,
// перетягивает внимание на себя. Номера строк и отступы внутри блока заданы в `em` и идут следом.
export const CODE_SIZES = [11, 12, 13, 14, 15, 16] as const

export const DEFAULT_CODE_SIZE = 12

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
