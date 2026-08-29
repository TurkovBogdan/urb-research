// Оформление схем в теле документа. Гарнитура схем живёт рядом, в `constants/fonts.ts`
// (`DIAGRAM_FONTS`): она часть шрифтового хозяйства, а здесь — раскладка блока со схемой.

export type DiagramAlign = 'left' | 'center'

export interface DiagramAlignOption {
  code: DiagramAlign
  label: string
  note: string
}

export const DIAGRAM_ALIGNS: DiagramAlignOption[] = [
  {
    code: 'left',
    label: 'По левому краю',
    note: 'Схема встаёт на ту же вертикаль, что и текст вокруг.',
  },
  {
    code: 'center',
    label: 'По центру',
    note: 'Схема заметнее, но узкая отрывается от колонки текста.',
  },
]

export const DEFAULT_DIAGRAM_ALIGN: DiagramAlign = 'left'

// Потолок высоты схемы в теле, в пикселях. Схема здесь — иллюстрация к тексту, и высокая
// вытесняет с экрана то, ради чего её открыли; разглядывают её в полноэкранном режиме.
// `0` — без потолка: схема показывается целиком, какой бы длинной ни была.
export const DIAGRAM_HEIGHTS = [280, 420, 560, 0] as const

export const DEFAULT_DIAGRAM_HEIGHT = 420

export const NO_DIAGRAM_HEIGHT = 0

// Неизвестное значение (устаревший ключ в localStorage, выпавший из набора вариант) откатывается
// к умолчанию, а не оставляет блок без выравнивания.
export function diagramAlign(code: string): DiagramAlign {
  return DIAGRAM_ALIGNS.some((option) => option.code === code)
    ? (code as DiagramAlign)
    : DEFAULT_DIAGRAM_ALIGN
}
