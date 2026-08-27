import { IconLayoutGrid, IconTable } from '@tabler/icons-vue'
import type { FunctionalComponent } from 'vue'

// Как показывать список исследований. Таблица по умолчанию: у исследования пять числовых
// счётчиков, а колонки — единственная раскладка, в которой их можно сравнить между строками.
// Карточки берут то же содержимое, но читаются как обзор, а не как сводка.

export type ResearchListView = 'table' | 'cards'

export const DEFAULT_RESEARCH_LIST_VIEW: ResearchListView = 'table'

export interface ResearchListViewOption {
  code: ResearchListView
  /** Ключ i18n: подпись в настройках и всплывающая — у переключателя на странице. */
  label: string
  icon: FunctionalComponent
}

export const RESEARCH_LIST_VIEWS: ResearchListViewOption[] = [
  { code: 'table', label: 'settings.interface.list.research.table', icon: IconTable },
  { code: 'cards', label: 'settings.interface.list.research.cards', icon: IconLayoutGrid },
]

/** Незнакомое значение (правили localStorage, откатили версию) не должно оставить список пустым. */
export function resolveResearchListView(value: string): ResearchListView {
  return RESEARCH_LIST_VIEWS.some((view) => view.code === value)
    ? (value as ResearchListView)
    : DEFAULT_RESEARCH_LIST_VIEW
}
