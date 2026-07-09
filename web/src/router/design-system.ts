import type { RouteRecordRaw } from 'vue-router'

export const designSystemRoutes: RouteRecordRaw[] = [
  { path: '/design-system', component: () => import('@/views/design-system/DesignSystemIndexView.vue'), meta: { scroll: 'y' } },
  {
    path: '/design-system/tokens',
    component: () => import('@/views/design-system/basics/TokensView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/typography',
    component: () => import('@/views/design-system/basics/TypographyView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/layout',
    component: () => import('@/views/design-system/basics/LayoutView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/breakpoints',
    component: () => import('@/views/design-system/responsive/BreakpointsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/action-panel',
    component: () => import('@/views/design-system/responsive/ActionPanelView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/buttons',
    component: () => import('@/views/design-system/controls/ButtonsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/button-group',
    component: () => import('@/views/design-system/controls/ButtonGroupView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/selects',
    component: () => import('@/views/design-system/controls/SelectsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/inputs',
    component: () => import('@/views/design-system/controls/InputsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/numbers',
    component: () => import('@/views/design-system/controls/NumbersView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/toggle',
    component: () => import('@/views/design-system/controls/ToggleView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/sliders',
    component: () => import('@/views/design-system/controls/SlidersView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/alerts',
    component: () => import('@/views/design-system/feedback/AlertsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/loaders',
    component: () => import('@/views/design-system/feedback/LoadersView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/skeleton',
    component: () => import('@/views/design-system/feedback/SkeletonView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/status-badge',
    component: () => import('@/views/design-system/feedback/StatusBadgeView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/chips',
    component: () => import('@/views/design-system/feedback/ChipsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/switch-panel',
    component: () => import('@/views/design-system/feedback/SwitchPanelView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/pagination',
    component: () => import('@/views/design-system/data/PaginationView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/data-table',
    component: () => import('@/views/design-system/data/DataTableView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/table',
    component: () => import('@/views/design-system/data/TableView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/dialogs',
    component: () => import('@/views/design-system/feedback/DialogsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/code-block',
    component: () => import('@/views/design-system/content/CodeBlockView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/markdown',
    component: () => import('@/views/design-system/content/MarkdownView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/chat',
    component: () => import('@/views/design-system/content/ChatView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/message',
    component: () => import('@/views/design-system/content/MessageContentView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/tooltips',
    component: () => import('@/views/design-system/feedback/TooltipsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/date-pickers',
    component: () => import('@/views/design-system/controls/DatePickersView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/dividers',
    component: () => import('@/views/design-system/structure/DividersView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/cards',
    component: () => import('@/views/design-system/structure/CardsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/file-cards',
    component: () => import('@/views/design-system/structure/FileCardsView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/spoiler',
    component: () => import('@/views/design-system/structure/SpoilerView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/members-cell',
    component: () => import('@/views/design-system/structure/MembersCellView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/world-map',
    component: () => import('@/views/design-system/data/WorldMapView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/line-chart',
    component: () => import('@/views/design-system/charts/LineChartView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/bar-chart',
    component: () => import('@/views/design-system/charts/BarChartView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/pie-chart',
    component: () => import('@/views/design-system/charts/PieChartView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/kanban',
    component: () => import('@/views/design-system/interface/KanbanView.vue'),
    meta: { scroll: 'y' },
  },
  {
    path: '/design-system/edge-scroller',
    component: () => import('@/views/design-system/interface/EdgeScrollerView.vue'),
    meta: { scroll: 'y' },
  },
]
