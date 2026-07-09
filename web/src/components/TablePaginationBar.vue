<script setup lang="ts">
import { computed } from 'vue'
import { useDisplay } from 'vuetify'

// Standardized table footer: "{range} of {total}" + per-page selector + pager.
// Replaces the hand-copied `.pagination-bar` block duplicated across list views.
// Responsive: below sm the row wraps — the range goes full-width (centered) and
// the selector + pager drop to a second centered line, and the pager shows
// fewer page buttons.

const props = withDefaults(defineProps<{
  page: number
  pageSize: number
  total: number
  pageCount: number
  pageSizes?: number[]
  divider?: boolean
}>(), {
  pageSizes: () => [25, 50, 100, 200],
  divider: true,
})

const emit = defineEmits<{
  'update:page': [value: number]
  'update:pageSize': [value: number]
}>()

const { smAndDown } = useDisplay()

// "1–50" (or "0" when empty) — the start–end span of the current page.
const rangeLabel = computed(() =>
  props.total === 0
    ? '0'
    : `${(props.page - 1) * props.pageSize + 1}–${Math.min(props.page * props.pageSize, props.total)}`,
)
</script>

<template>
  <!-- Single root so a parent-passed class (e.g. `mt-3`) inherits; two roots
       (divider + bar) made it a fragment → class was dropped + Vue warned. -->
  <div class="pagination-bar-root">
    <VDivider v-if="divider" />
    <div class="pagination-bar">
    <span class="mono pagination-bar__count">
      {{ rangeLabel }} {{ $t('common.pagination.of') }} {{ total }}
    </span>
    <VSelect
      :model-value="pageSize"
      :items="pageSizes"
      :label="$t('common.pagination.per_page')"
      density="comfortable"
      variant="outlined"
      hide-details
      class="pagination-bar__size"
      @update:model-value="emit('update:pageSize', $event)"
    />
    <VPagination
      :model-value="page"
      :length="pageCount"
      :total-visible="smAndDown ? 3 : 5"
      density="comfortable"
      class="pagination-bar__pager"
      @update:model-value="emit('update:page', $event)"
    />
    <!-- Mobile-only: splits the pager (top) from the count|selector row below. -->
    <VDivider class="pagination-bar__split" />
    </div>
  </div>
</template>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 10px 12px;
}

/* margin-inline-end:auto replaces the old <VSpacer/> — pushes the selector and
   pager to the right edge while the range hugs the left. */
.pagination-bar__count {
  font-size: 11px;
  color: var(--text-faint);
  margin-inline-end: auto;
}

.pagination-bar__size {
  max-width: 130px;
}

/* Inner divider is mobile-only (see media query). */
.pagination-bar__split {
  display: none;
}

/* Phones (< sm): pager on top, a divider, then count (left corner) | selector
   (right corner) on one row. Reordered via `order`; the count's
   margin-inline-end:auto pushes the selector to the opposite corner. */
@media (max-width: 599px) {
  .pagination-bar {
    justify-content: flex-start;
    gap: 10px 12px;
  }
  .pagination-bar__pager {
    order: 1;
    width: 100%;
  }
  .pagination-bar__split {
    order: 2;
    display: block;
    width: 100%;
    margin: 0;
  }
  .pagination-bar__count {
    order: 3;
  }
  .pagination-bar__size {
    order: 4;
  }
}

.mono {
  font-family: var(--font-mono);
}
</style>
