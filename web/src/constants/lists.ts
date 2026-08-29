import { IconFolders, IconTable } from '@tabler/icons-vue'
import type { FunctionalComponent } from 'vue'

// Как показывать список исследований. Таблица по умолчанию: у исследования пять числовых
// счётчиков, а колонки — единственная раскладка, в которой их можно сравнить между строками.
// Плитки — всегда по полкам: сами по себе они давали общий поток, который таблица показывает
// плотнее и с теми же данными, поэтому от плиток нужен ровно состав полок.

export type ResearchListView = 'table' | 'grouped'

export const DEFAULT_RESEARCH_LIST_VIEW: ResearchListView = 'table'

export interface ResearchListViewOption {
  code: ResearchListView
  /** Ключ i18n: подпись в настройках и всплывающая — у переключателя на странице. */
  label: string
  icon: FunctionalComponent
}

export const RESEARCH_LIST_VIEWS: ResearchListViewOption[] = [
  { code: 'table', label: 'settings.interface.list.research.table', icon: IconTable },
  { code: 'grouped', label: 'settings.interface.list.research.grouped', icon: IconFolders },
]

// Размеры страницы у списков исследований. Начинаются с 200, потому что строка реестра — это
// название, описание и пять счётчиков: весь реестр помещается в одну страницу, и мельчить её
// значило бы заставлять листать там, где листать нечего. Первое значение — умолчание.
// У остальных таблиц проекта (источники, страницы веб-поиска, запуски задач) лестница своя,
// стандартная: там строка тянет за собой материал.
export const RESEARCH_PAGE_SIZES = [200, 500, 1000]

/** Незнакомое значение (правили localStorage, откатили версию) не должно оставить список пустым. */
export function resolveResearchListView(value: string): ResearchListView {
  return RESEARCH_LIST_VIEWS.some((view) => view.code === value)
    ? (value as ResearchListView)
    : DEFAULT_RESEARCH_LIST_VIEW
}
