import type { RouteRecordRaw } from 'vue-router'

// Витрина дизайн-системы: сорок страниц одной формы (ленивый компонент + вертикальный скролл),
// поэтому маршруты собираются из таблицы «сегмент адреса → файл вьюхи», а не пишутся по одному.
// Тот же сегмент — ключ словаря `design-system.index.page.<slug>.label`, по нему же страницы
// перечислены на индексной странице, так что второго списка имён не заводится.
const PAGES: Record<string, string> = {
  tokens:          'basics/TokensView',
  typography:      'basics/TypographyView',
  layout:          'basics/LayoutView',
  breakpoints:     'responsive/BreakpointsView',
  'action-panel':  'responsive/ActionPanelView',
  buttons:         'controls/ButtonsView',
  'button-group':  'controls/ButtonGroupView',
  selects:         'controls/SelectsView',
  inputs:          'controls/InputsView',
  'search-field':  'controls/SearchFieldView',
  numbers:         'controls/NumbersView',
  toggle:          'controls/ToggleView',
  sliders:         'controls/SlidersView',
  'date-pickers':  'controls/DatePickersView',
  'icon-picker':   'controls/IconPickerView',
  'color-picker':  'controls/ColorPickerView',
  'icon-color-picker': 'controls/IconColorPickerView',
  'table-page':    'tables/TablePageView',
  'data-table':    'tables/DataTableView',
  table:           'tables/TableView',
  pagination:      'tables/PaginationView',
  'line-chart':    'charts/LineChartView',
  'bar-chart':     'charts/BarChartView',
  'pie-chart':     'charts/PieChartView',
  'world-map':     'charts/WorldMapView',
  alerts:          'feedback/AlertsView',
  toasts:          'feedback/ToastsView',
  callout:         'feedback/CalloutView',
  'error-states':  'feedback/ErrorStatesView',
  loaders:         'feedback/LoadersView',
  skeleton:        'feedback/SkeletonView',
  'status-badge':  'feedback/StatusBadgeView',
  chips:           'feedback/ChipsView',
  'switch-panel':  'feedback/SwitchPanelView',
  dialogs:         'feedback/DialogsView',
  tooltips:        'feedback/TooltipsView',
  'code-block':    'content/CodeBlockView',
  markdown:        'content/MarkdownView',
  chat:            'content/ChatView',
  message:         'content/MessageContentView',
  dividers:        'structure/DividersView',
  cards:           'structure/CardsView',
  'file-cards':    'structure/FileCardsView',
  spoiler:         'structure/SpoilerView',
  'members-cell':  'structure/MembersCellView',
  'page-header':   'structure/PageHeaderView',
  'detail-nav':    'structure/DetailNavView',
  'section-header': 'structure/SectionHeaderView',
  kanban:          'interface/KanbanView',
  'edge-scroller': 'interface/EdgeScrollerView',
  'research-card': 'project/ResearchCardView',
  'group-select':  'project/GroupSelectView',
}

// Статический глоб: путь к вьюхе — переменная, а сборщику нужен разбираемый шаблон.
const views = import.meta.glob('../views/design-system/**/*.vue')

export const designSystemRoutes: RouteRecordRaw[] = [
  {
    path: '/design-system',
    name: 'design-system',
    component: () => import('@/views/design-system/DesignSystemIndexView.vue'),
    meta: { scroll: 'y', title: 'design-system.nav' },
  },
  ...Object.entries(PAGES).map(([slug, file]): RouteRecordRaw => ({
    path: `/design-system/${slug}`,
    name: `design-system-${slug}`,
    component: views[`../views/design-system/${file}.vue`],
    meta: { scroll: 'y', title: `design-system.index.page.${slug}.label` },
  })),
]
