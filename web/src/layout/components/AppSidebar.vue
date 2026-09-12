<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDisplay } from 'vuetify'
import { IconChevronRight, IconChevronLeft } from '@tabler/icons-vue'

import { useLayoutStore } from '../store'
import { useSettingsStore } from '@/stores/settings'
import { isGroup, isSection, type NavEntry, type NavLink, type NavSection, type NavSectionEntry } from '@/shared/nav'
import { IconPalette, IconServerCog, IconAdjustments, IconWorldSearch, IconListSearch, IconFileText, IconClock, IconServerBolt, IconTelescope, IconPlugConnected, IconTypography, IconCategory, IconInfoCircle } from '@tabler/icons-vue'

const layout = useLayoutStore()
const settings = useSettingsStore()
const route  = useRoute()
const { t } = useI18n()
const { mobile } = useDisplay()

// On mobile the drawer is a temporary overlay: never collapse to the rail (always
// full width), toggled via `layout.mobileOpen`. The desktop collapse state is
// ignored while mobile.
const collapsed = computed(() => !mobile.value && settings.ui.sidebarCollapsed)

// Drawer open/close. Desktop permanent drawer is always "open"; mobile overlay
// follows the shared store flag (set by the top-bar hamburger).
const drawerOpen = computed({
  get: () => (mobile.value ? layout.mobileOpen : true),
  set: (v) => { layout.mobileOpen = v },
})

// Navigating closes the overlay (any nav click / programmatic push).
watch(() => route.path, () => { if (mobile.value) layout.mobileOpen = false })

function navLabel(entry: { label: string; labelKey?: string }): string {
  return entry.labelKey ? t(entry.labelKey) : entry.label
}

const navSections: NavSection[] = [
  { kind: 'section', code: 'mcp', labelKey: 'common.nav.mcp', order: 10 },
  { kind: 'section', code: 'research', labelKey: 'common.nav.research', order: 20 },
  { kind: 'section', code: 'data', labelKey: 'common.nav.data', order: 30 },
  { kind: 'section', code: 'settings', labelKey: 'common.nav.settings', order: 40 },
  { kind: 'section', code: 'about', labelKey: 'common.nav.about', order: 50 },
  { kind: 'section', code: 'development', labelKey: 'common.nav.development', order: 60 },
]

const navEntries: NavSectionEntry[] = [
  { section: 'mcp', order: 10, path: '/mcp-servers', label: 'MCP-серверы', labelKey: 'core_mcp.nav', icon: IconServerBolt },
  { section: 'research', order: 10, path: '/research/groups', label: 'Группы', labelKey: 'research.nav_groups', icon: IconCategory },
  { section: 'research', order: 20, path: '/research/researches', label: 'Исследования', labelKey: 'research.nav', icon: IconTelescope },
  {
    section: 'data',
    order: 10,
    label: 'Веб-поиск',
    labelKey: 'web_search.nav',
    icon: IconWorldSearch,
    children: [
      { path: '/web-search/queries', label: 'Запросы', labelKey: 'web_search.nav_queries', icon: IconListSearch },
      { path: '/web-search/pages', label: 'Страницы', labelKey: 'web_search.nav_pages', icon: IconFileText },
    ],
  },
  { section: 'settings', order: 10, path: '/settings/interface', label: 'Интерфейс', icon: IconTypography },
  { section: 'settings', order: 20, path: '/integrations', label: 'Интеграции', labelKey: 'core_connectors.nav', icon: IconPlugConnected },
  { section: 'settings', order: 30, path: '/settings/modules', label: 'Модули', icon: IconAdjustments },
  { section: 'settings', order: 40, path: '/tasks', label: 'Задачи', labelKey: 'core_monitoring.nav', icon: IconClock },
  { section: 'settings', order: 50, path: '/settings/core', label: 'Сервер', labelKey: 'setup.nav', icon: IconServerCog },
  { section: 'about', order: 10, path: '/about', label: 'Версия и обновление', labelKey: 'about.nav', icon: IconInfoCircle },
  // design-system is template chrome (not a module) — link inlined.
  { section: 'development', order: 10, path: '/design-system', label: 'Дизайн-система', labelKey: 'design-system.nav', icon: IconPalette },
]

const navBottom: NavLink[] = []

const byOrder = (a: { order: number }, b: { order: number }) => a.order - b.order

// Раздел без записей не показывается: остался бы висячий заголовок с разделителем.
const visibleNav = computed<NavEntry[]>(() =>
  [...navSections].sort(byOrder).flatMap(section => {
    const sectionEntries = navEntries.filter(entry => entry.section === section.code).sort(byOrder)
    return sectionEntries.length ? [section, ...sectionEntries] : []
  }),
)

const visibleNavBottom = computed<NavLink[]>(() => navBottom)

// Подсветка по ПРЕФИКСУ, а не по точному совпадению: деталка (`/research/researches/<code>`)
// принадлежит своему разделу, и раньше на ней в меню не было подсвечено ничего.
function isActive(navPath: string) {
  return route.path === navPath || route.path.startsWith(navPath + '/')
}

function isGroupActive(group: NavEntry): boolean {
  return isGroup(group) && group.children.some(c => isActive(c.path))
}

const openGroups = ref<Record<string, boolean>>(
  Object.fromEntries(
    navEntries.filter(isGroup).map(g => [g.label, isGroupActive(g)]),
  ),
)

const drawerWidth = computed(() => (mobile.value ? 280 : collapsed.value ? 56 : 250))
</script>

<template>
  <VNavigationDrawer
    v-model="drawerOpen"
    :permanent="!mobile"
    :temporary="mobile"
    :width="drawerWidth"
    color="surface-variant"
    class="app-sidebar"
    :class="{ 'app-sidebar--collapsed': collapsed }"
  >
    <!-- Desktop only: brand + rail collapse toggle. On mobile the brand lives in the
         top app-bar (no duplication) and the drawer opens straight to the nav list. -->
    <template v-if="!mobile" #prepend>
      <div class="sidebar-logo" :class="{ 'sidebar-logo--collapsed': collapsed }">
        <template v-if="!collapsed">
          <RouterLink to="/home" class="logo-link">
            <span class="logo-icon">◈</span>
            <span class="logo-text">Uroboros.Research</span>
          </RouterLink>
        </template>
        <VBtn
          :icon="collapsed ? IconChevronRight : IconChevronLeft"
          variant="text"
          density="compact"
          size="small"
          class="collapse-btn"
          @click="settings.ui.sidebarCollapsed = !settings.ui.sidebarCollapsed"
        />
      </div>

      <VDivider class="sidebar-divider" />
    </template>

    <VList
      density="compact"
      nav
      class="sidebar-nav"
      :class="{ 'sidebar-nav--collapsed': collapsed }"
    >
      <!-- ── Collapsed: groups → parent icon + flyout, links → tooltip ── -->
      <template v-if="collapsed">
        <template v-for="(entry, idx) in visibleNav" :key="isSection(entry) ? `s-${idx}` : isGroup(entry) ? entry.label : entry.path">

          <template v-if="isSection(entry)">
            <VDivider
              v-if="idx > 0"
              class="sidebar-section-divider"
            />
          </template>

          <VMenu
            v-else-if="isGroup(entry)"
            location="end"
            :offset="8"
            open-on-click
            close-on-content-click
          >
            <template #activator="{ props }">
              <VListItem
                v-bind="props"
                :active="isGroupActive(entry)"
                :prepend-icon="entry.icon"
                rounded="lg"
                class="nav-item nav-item--collapsed"
              />
            </template>

            <div class="nav-flyout">
              <div class="nav-flyout__title">{{ navLabel(entry) }}</div>
              <VList density="compact" nav class="nav-flyout__list">
                <VListItem
                  v-for="child in entry.children"
                  :key="child.path"
                  :to="child.path"
                  :active="isActive(child.path)"
                  :prepend-icon="child.icon"
                  :title="navLabel(child)"
                  rounded="lg"
                  class="nav-item"
                />
              </VList>
            </div>
          </VMenu>

          <VTooltip
            v-else
            :text="navLabel(entry)"
            location="end"
            :offset="6"
            content-class="sidebar-tooltip"
          >
            <template #activator="{ props }">
              <VListItem
                v-bind="props"
                :to="entry.path"
                :active="isActive(entry.path)"
                :prepend-icon="entry.icon"
                rounded="lg"
                class="nav-item nav-item--collapsed"
              />
            </template>
          </VTooltip>

        </template>
      </template>

      <!-- ── Expanded ── -->
      <template v-else>
        <template v-for="(entry, idx) in visibleNav" :key="isSection(entry) ? `s-${idx}` : isGroup(entry) ? entry.label : entry.path">
          <div
            v-if="isSection(entry)"
            class="nav-section"
          >
            {{ t(entry.labelKey) }}
          </div>

          <VListGroup
            v-else-if="isGroup(entry)"
            v-model="openGroups[entry.label]"
          >
            <template #activator="{ props }">
              <VListItem
                v-bind="props"
                :prepend-icon="entry.icon"
                :title="navLabel(entry)"
                :active="isGroupActive(entry)"
                rounded="lg"
                class="nav-item nav-group-activator"
              />
            </template>

            <VListItem
              v-for="child in entry.children"
              :key="child.path"
              :to="child.path"
              :active="isActive(child.path)"
              :prepend-icon="child.icon"
              :title="navLabel(child)"
              rounded="lg"
              class="nav-item nav-item--child"
            />
          </VListGroup>

          <VListItem
            v-else
            :to="entry.path"
            :active="isActive(entry.path)"
            :prepend-icon="entry.icon"
            :title="navLabel(entry)"
            rounded="lg"
            class="nav-item"
          />
        </template>
      </template>
    </VList>

    <template #append>
      <template v-if="visibleNavBottom.length">
      <VDivider class="sidebar-divider" />
      <VList
        density="compact"
        nav
        class="sidebar-nav pb-2"
        :class="{ 'sidebar-nav--collapsed': collapsed }"
      >
        <VTooltip
          v-for="item in visibleNavBottom"
          :key="item.path"
          :text="navLabel(item)"
          location="end"
          :offset="6"
          :disabled="!collapsed"
          content-class="sidebar-tooltip"
        >
          <template #activator="{ props }">
            <VListItem
              v-bind="props"
              :to="item.path"
              :active="isActive(item.path)"
              :prepend-icon="item.icon"
              :title="collapsed ? '' : navLabel(item)"
              rounded="lg"
              class="nav-item"
              :class="{ 'nav-item--collapsed': collapsed }"
            />
          </template>
        </VTooltip>

      </VList>
      </template>
    </template>
  </VNavigationDrawer>
</template>

<style scoped>
.logo-link {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
  text-align: left;
  text-decoration: none;
}

</style>
