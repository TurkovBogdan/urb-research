<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

// Табличная ячейка участников: показывает первого, остальные прячет за плашкой «+N»,
// которая по клику раскрывает тултип-попап со всем списком. Каждый пункт кликабелен —
// компонент эмитит `select` с индексом, действие выбирает родитель (фильтр по контакту,
// по участнику команды и т.п.). Источник паттерна — список оригинальных чатов.
export interface MemberCellItem {
  // Основная подпись (имя или email).
  label: string
  // Вторичная строка в попапе (email/телефон); показывается только если отличается от label.
  sub?: string | null
  // Некликабельный пункт (нечем фильтровать) — заголовок виден, клик не эмитится.
  disabled?: boolean
}

const props = withDefaults(defineProps<{
  items: MemberCellItem[]
  // Подпись пустой ячейки (нет участников).
  emptyText?: string
  // Курсивная приглушённая пустая подпись (напр. «Нет команды»).
  emptyItalic?: boolean
  // Заголовок попапа; по умолчанию — общая подсказка «Нажмите чтобы применить фильтр».
  hint?: string
  // Моноширинный текст подписей (для email-колонок).
  mono?: boolean
  // Длина обрезки видимой подписи.
  max?: number
}>(), {
  emptyText: '—',
  emptyItalic: false,
  mono: false,
  max: 32,
})

const emit = defineEmits<{ (e: 'select', index: number): void }>()

const { t } = useI18n()

const hintText = computed(() => props.hint ?? t('common.members_cell.hint'))
const first = computed(() => props.items[0])
const extra = computed(() => props.items.length - 1)

function truncate(value: string): string {
  return value.length > props.max ? value.slice(0, props.max).trimEnd() + '…' : value
}

function pick(index: number): void {
  if (props.items[index]?.disabled) return
  emit('select', index)
}
</script>

<template>
  <div class="members-cell">
    <template v-if="first">
      <a
        v-if="!first.disabled"
        class="members-cell__link"
        :class="{ 'members-cell--mono': mono }"
        :title="first.sub || first.label"
        @click.stop="pick(0)"
      >{{ truncate(first.label) }}</a>
      <span
        v-else
        class="members-cell__plain"
        :class="{ 'members-cell--mono': mono }"
        :title="first.label"
      >{{ truncate(first.label) }}</span>

      <VMenu
        v-if="extra > 0"
        location="bottom start"
        offset="8"
        content-class="members-cell-menu"
        :close-on-content-click="true"
      >
        <template #activator="{ props: menuProps }">
          <VChip
            v-bind="menuProps"
            size="x-small"
            variant="tonal"
            color="primary"
            class="members-cell__more"
            @click.stop
          >
            +{{ extra }}
          </VChip>
        </template>
        <div class="members-popover">
          <div class="members-popover__hint">{{ hintText }}</div>
          <VList density="compact" class="members-popover__list">
            <VListItem
              v-for="(m, i) in items"
              :key="i"
              :disabled="m.disabled"
              @click.stop="pick(i)"
            >
              <VListItemTitle class="members-popover__name" :class="{ 'members-cell--mono': mono }">{{ m.label }}</VListItemTitle>
              <VListItemSubtitle
                v-if="m.sub && m.sub !== m.label"
                class="members-popover__sub"
                :class="{ 'members-cell--mono': mono }"
              >{{ m.sub }}</VListItemSubtitle>
            </VListItem>
          </VList>
        </div>
      </VMenu>
    </template>

    <span
      v-else
      class="members-cell__empty"
      :class="{ 'members-cell__empty--italic': emptyItalic }"
    >{{ emptyText }}</span>
  </div>
</template>

<style scoped>
.members-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.members-cell__link {
  font-size: 12px;
  color: var(--accent, rgb(var(--v-theme-primary)));
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.members-cell__link:hover { text-decoration: underline; }

.members-cell__plain {
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.members-cell__empty { color: var(--text-faint); }
.members-cell__empty--italic { font-style: italic; }

.members-cell__more {
  cursor: pointer;
  flex: 0 0 auto;
  transition: background-color .15s ease, color .15s ease;
}

.members-cell__more:hover {
  background: var(--accent) !important;
  color: #fff !important;
}

.members-cell--mono { font-family: var(--font-mono); }

/* ── Popover (tooltip bubble with an arrow) ─────────────────────────── */

.members-popover {
  position: relative;
  min-width: 220px;
  max-width: 380px;
  overflow: visible;
  background: rgb(var(--v-theme-surface));
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  /* drop-shadow (не box-shadow): тень повторяет контур вместе со стрелкой-псевдоэлементом. */
  filter: drop-shadow(0 6px 18px rgb(0 0 0 / 14%));
}

/* Стрелочка: повёрнутый квадрат у верхнего края, под активатором (location=bottom start).
   Верхняя и левая кромки несут рамку — это остриё над верхним бордером попапа. */
.members-popover::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 16px;
  width: 10px;
  height: 10px;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid var(--border-soft);
  border-left: 1px solid var(--border-soft);
  transform: rotate(45deg);
}

.members-popover__hint {
  padding: 8px 14px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-soft);
  border-radius: 7px 7px 0 0;
}

.members-popover__list {
  background: transparent;
  padding: 4px 6px 6px;
  max-height: 320px;
  overflow-y: auto;
  border-radius: 0 0 7px 7px;
}

.members-popover__name {
  font-size: 13px;
  color: var(--text);
}

.members-popover__sub {
  font-size: 12px;
  color: var(--text-faint);
}
</style>

<!-- Menu content is teleported outside the component, so these overrides can't be scoped —
     keep them global, namespaced by the menu's content-class. The inner `.v-list` otherwise
     inherits the global dropdown-card styling (surface bg + border + shadow), stacking a
     second panel inside `.members-popover`; the extra `.v-list` qualifier outscores that
     `!important` rule so the list stays flat. -->
<style>
.members-cell-menu.v-overlay__content { overflow: visible; }

.v-menu .members-cell-menu .members-popover__list.v-list {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

/* Фирменное (primary) выделение пункта на hover — overlay по умолчанию серый (on-surface). */
.members-cell-menu .v-list-item--link:hover > .v-list-item__overlay {
  background: rgb(var(--v-theme-primary));
}
</style>
