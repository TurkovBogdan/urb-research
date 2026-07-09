import type { FunctionalComponent, SVGAttributes } from 'vue'

export type TablerIcon = FunctionalComponent<SVGAttributes>

export type NavLink = {
  path: string
  label: string
  labelKey?: string
  icon: TablerIcon
}

export type NavGroup = {
  label: string
  labelKey?: string
  icon: TablerIcon
  children: NavLink[]
}

export type NavSection = {
  kind: 'section'
  label: string
  labelKey?: string
}

export type NavEntry = NavLink | NavGroup | NavSection

export function isGroup(entry: NavEntry): entry is NavGroup {
  return 'children' in entry
}

export function isSection(entry: NavEntry): entry is NavSection {
  return (entry as NavSection).kind === 'section'
}
