<script setup lang="ts">
/**
 * VSelect with a search row pinned atop the open menu.
 *
 * Vuetify has no built-in for this — VAutocomplete merges the query into the field,
 * which changes the field display. VSelectSearch keeps the field untouched and filters
 * the items in place via the #prepend-item slot. All VSelect props/slots pass through
 * ($attrs + slot forwarding), so it's a drop-in replacement: swap VSelect → VSelectSearch.
 */
import { computed, ref, useSlots } from 'vue'
import { IconSearch } from '@tabler/icons-vue'

const model = defineModel<unknown>()

const props = withDefaults(defineProps<{
  items: unknown[]
  /** Property read as the display title for object items (mirrors VSelect's item-title). */
  itemTitle?: string
  /** Placeholder for the in-dropdown search field. */
  searchPlaceholder?: string
  /** Text shown when the filter matches nothing. */
  noDataText?: string
}>(), {
  itemTitle: 'title',
  searchPlaceholder: 'Search…',
  noDataText: 'Nothing found',
})

defineOptions({ inheritAttrs: false })

const search = ref('')

function titleOf(item: unknown): string {
  if (item != null && typeof item === 'object') {
    return String((item as Record<string, unknown>)[props.itemTitle] ?? '')
  }
  return String(item ?? '')
}

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.items
  return props.items.filter(it => titleOf(it).toLowerCase().includes(q))
})

// Clear the query when the menu closes so it reopens clean.
function onMenuToggle(open: boolean) {
  if (!open) search.value = ''
}

// Forward every consumer slot to VSelect except the two we own (prepend-item / no-data).
const slots = useSlots()
const forwardedSlots = computed(() =>
  Object.keys(slots).filter(name => name !== 'prepend-item' && name !== 'no-data'),
)
</script>

<template>
  <VSelect
    v-bind="$attrs"
    v-model="model"
    :items="filtered"
    :item-title="itemTitle"
    @update:menu="onMenuToggle"
  >
    <template #prepend-item>
      <div class="vss-search">
        <VTextField
          v-model="search"
          :prepend-inner-icon="IconSearch"
          :placeholder="searchPlaceholder"
          variant="plain"
          density="compact"
          autofocus
          hide-details
          @keydown.stop
        />
      </div>
      <VDivider />
    </template>

    <template #no-data>
      <div class="vss-empty">{{ noDataText }}</div>
    </template>

    <template v-for="name in forwardedSlots" #[name]="slotProps" :key="name">
      <slot :name="name" v-bind="slotProps ?? {}" />
    </template>
  </VSelect>
</template>

<style scoped>
/* Search row + empty state live in the teleported menu — scope id still reaches them. */
.vss-search {
  padding: 4px 10px 6px;
}

.vss-empty {
  padding: 10px 16px;
  font-size: 13px;
  color: var(--text-faint);
}
</style>
