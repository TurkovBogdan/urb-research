<script setup lang="ts">
/**
 * A "Source" panel — links back to a record's external origin (e.g. an external
 * service thread). The caller maps its domain data into `items` (records shown directly) and the
 * optional `others` (collapsed behind a spoiler). When `items` is empty, `emptyText` is
 * shown as a warning plate.
 *
 * Thread numbering is owned here: an item that carries an `activity` timestamp gets a
 * localized "Thread #N · updated <when>" subtitle. Numbering restarts per owner (`group`)
 * and ranks that owner's dated threads by ascending activity — the oldest is #1. Items
 * sharing no `group` are numbered together. Items that instead pass an explicit `subtitle`
 * (no activity) render it verbatim.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconAlertTriangle } from '@tabler/icons-vue'
import { fmtRelative } from '@/shared/utils/date'
import Spoiler from '@/components/Spoiler.vue'
import SourceLinkRow from '@/components/SourceLinkRow.vue'

export interface SourceLinkItem {
  url: string
  title: string
  subtitle?: string
  activity?: string | null
  group?: string
}

const props = withDefaults(defineProps<{
  items: SourceLinkItem[]
  others?: SourceLinkItem[]
  title?: string
  emptyText?: string
  othersTitle?: string
}>(), {
  others: () => [],
})

const { t } = useI18n()

const threadNumberByItem = computed(() => {
  const byOwner = new Map<string, SourceLinkItem[]>()
  for (const item of [...props.items, ...props.others]) {
    if (!item.activity) continue
    const owner = item.group ?? ''
    const group = byOwner.get(owner) ?? []
    group.push(item)
    byOwner.set(owner, group)
  }
  const numbers = new Map<SourceLinkItem, number>()
  for (const group of byOwner.values()) {
    group.sort((a, b) => (a.activity! < b.activity! ? -1 : 1))
    group.forEach((item, index) => numbers.set(item, index + 1))
  }
  return numbers
})

function rowSubtitle(item: SourceLinkItem): string | undefined {
  if (!item.activity) return item.subtitle
  return t('common.source.thread_updated', {
    number: threadNumberByItem.value.get(item),
    date: fmtRelative(item.activity),
  })
}
</script>

<template>
  <section class="source-links">
    <div v-if="title" class="source-links__header">{{ title }}</div>

    <SourceLinkRow
      v-for="(item, i) in items"
      :key="i"
      :url="item.url"
      :title="item.title"
      :subtitle="rowSubtitle(item)"
    />

    <div v-if="!items.length && emptyText" class="source-links__empty">
      <VIcon :icon="IconAlertTriangle" size="16" />
      <span>{{ emptyText }}</span>
    </div>

    <Spoiler
      v-if="others.length"
      variant="minimal"
      :title="othersTitle"
      class="source-links__spoiler"
    >
      <SourceLinkRow
        v-for="(item, i) in others"
        :key="i"
        :url="item.url"
        :title="item.title"
        :subtitle="rowSubtitle(item)"
      />
    </Spoiler>
  </section>
</template>

<style scoped>
.source-links { padding: 4px 0; }

.source-links__header {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 16px 4px;
}

.source-links__empty {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 16px 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(var(--v-theme-warning), 0.10);
  color: rgb(var(--v-theme-warning));
  font-size: 12px;
}

.source-links__spoiler :deep(.spoiler__head) {
  padding: 4px 16px;
}

.source-links__spoiler :deep(.spoiler__content) {
  padding: 4px 0 8px;
}
</style>
