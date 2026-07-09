<script setup lang="ts">
import { IconArrowLeft } from '@tabler/icons-vue'
import { useRouter, type RouteLocationRaw } from 'vue-router'
import { useNavigationHistory } from '@/composables/useNavigationHistory'

const props = defineProps<{
  title: string
  description?: string
  backTo?: RouteLocationRaw
  loading?: boolean
}>()

const router = useRouter()
const { goBack } = useNavigationHistory()
</script>

<template>
  <div class="page-header">
    <div v-if="$slots.before || backTo" class="page-header__before">
      <slot name="before">
        <VBtn
          :icon="IconArrowLeft"
          variant="tonal"
          density="default"
          rounded="0"
          @click="goBack(router, props.backTo!)"
        />
      </slot>
    </div>
    <div class="page-header__left">
      <template v-if="loading">
        <VSkeletonLoader type="heading" class="page-header__skel page-header__skel--title" />
        <VSkeletonLoader type="text" class="page-header__skel page-header__skel--desc" />
      </template>
      <template v-else>
        <h1 class="page-header__title">{{ title }}</h1>
        <p v-if="description || $slots.description" class="page-header__desc">
          <slot name="description">{{ description }}</slot>
        </p>
      </template>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: nowrap;
}

.page-header__before + .page-header__left {
  margin-left: -8px;
}

.page-header__before {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.page-header__left {
  flex: 1;
  min-width: 0;
}

.page-header__title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text);
  line-height: 1.3;
  margin: 0;
}

.page-header__desc {
  margin: 3px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  max-width: 640px;
}

/* Loading placeholders mirroring title + description sizes. Vuetify sets the bone width
   inline (100% of the loader), so we constrain the loader root width instead and only
   tweak the bone height/margin. */
.page-header__skel { padding: 0; background: transparent; }
.page-header__skel--title { width: 280px; max-width: 55%; }
.page-header__skel--desc  { width: 180px; max-width: 38%; }
.page-header__skel--title :deep(.v-skeleton-loader__bone) { height: 16px; margin: 3px 0; }
.page-header__skel--desc  :deep(.v-skeleton-loader__bone) { height: 10px; margin: 8px 0 0; }

.page-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

@media (max-width: 959px) {
  .page-header {
    flex-wrap: wrap;
  }

  .page-header__left {
    width: 100%;
  }

  .page-header__actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
