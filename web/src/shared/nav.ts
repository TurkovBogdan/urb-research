import type { FunctionalComponent, SVGAttributes } from 'vue'

export type TablerIcon = FunctionalComponent<SVGAttributes>

export type NavPlacement = {
  section: string
  order: number
}

export type NavLink = {
  path: string
  label: string
  labelKey?: string
  icon: TablerIcon
}

export type NavSectionLink = NavLink & NavPlacement

export type NavGroup = NavPlacement & {
  label: string
  labelKey?: string
  icon: TablerIcon
  children: NavLink[]
}

export type NavSection = {
  kind: 'section'
  code: string
  labelKey: string
  order: number
}

export type NavSectionEntry = NavSectionLink | NavGroup

export type NavEntry = NavSectionEntry | NavSection

export function isGroup(entry: NavEntry): entry is NavGroup {
  return 'children' in entry
}

export function isSection(entry: NavEntry): entry is NavSection {
  return (entry as NavSection).kind === 'section'
}
