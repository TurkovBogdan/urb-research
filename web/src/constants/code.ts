// Вид блока кода в теле документа. Компонент `CodeBlock` умеет четыре вида, но выбирают из трёх:
// `compact` (однострочная командная плашка) не выбор человека, а следствие содержимого — фенс в
// одну строку рисуется ею всегда.

export type CodeVariant = 'icon' | 'accent' | 'minimal'

export interface CodeVariantOption {
  code: CodeVariant
  label: string
  note: string
}

export const CODE_VARIANTS: CodeVariantOption[] = [
  {
    code: 'icon',
    label: 'Шапка со значками',
    note: 'Ярлык языка слева, значки нумерации и копирования справа.',
  },
  {
    code: 'accent',
    label: 'Шапка с кнопкой',
    note: 'Тот же ярлык языка, но копирование — заметной кнопкой с подписью.',
  },
  {
    code: 'minimal',
    label: 'Без шапки',
    note: 'Только подсвеченный код: ни языка, ни кнопок. Копировать придётся выделением.',
  },
]

export const DEFAULT_CODE_VARIANT: CodeVariant = 'minimal'

// Неизвестное значение (устаревший ключ в кеше браузера, выпавший из набора вид) откатывается к
// умолчанию, а не оставляет блок без вида.
export function codeVariant(code: string): CodeVariant {
  return CODE_VARIANTS.some((option) => option.code === code)
    ? (code as CodeVariant)
    : DEFAULT_CODE_VARIANT
}
