<script setup lang="ts">
import EdgeScroller from '@/layout/components/EdgeScroller.vue'

// Kanban board = a horizontal row of columns. The scroll/bleed/edge-shadow shell
// is EdgeScroller; this just lays the slotted <KanbanColumn>s out in a flex track.
</script>

<template>
  <EdgeScroller bleed>
    <div class="kanban-track">
      <slot />
    </div>
  </EdgeScroller>
</template>

<style scoped>
.kanban-track {
  display: flex;
  gap: 14px;
}
</style>
