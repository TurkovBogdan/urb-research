<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const progress = ref(65)
const buffer   = ref(80)

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.loaders.title')" :description="t('design-system.page.loaders.description')" back-to="/design-system" />

    <!-- VProgressCircular -->
    <section class="ds-section">
      <h6 class="mb-3">VProgressCircular</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">indeterminate</span>
          <div class="ds-controls">
            <VProgressCircular indeterminate size="24" width="2" />
          </div>
          <span class="ds-spec">indeterminate</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">determinate</span>
          <div class="ds-controls">
            <VProgressCircular :model-value="progress" size="24" width="2" />
          </div>
          <span class="ds-spec">:model-value="{{ progress }}"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">sizes</span>
          <div class="ds-controls">
            <VProgressCircular indeterminate size="16" width="2" />
            <VProgressCircular indeterminate size="24" width="2" />
            <VProgressCircular indeterminate size="32" width="3" />
            <VProgressCircular indeterminate size="48" width="3" />
          </div>
          <span class="ds-spec">16 / 24 / 32 / 48</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">in button</span>
          <div class="ds-controls">
            <VBtn :loading="true" size="small">Loading</VBtn>
            <VBtn :loading="true" size="default">Loading</VBtn>
            <VBtn :loading="true" variant="outlined" size="small">Loading</VBtn>
          </div>
          <span class="ds-spec">:loading="true"</span>
        </div>

      </div>
    </section>

    <!-- VProgressLinear -->
    <section class="ds-section">
      <h6 class="mb-3">VProgressLinear</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">indeterminate</span>
          <div class="ds-controls ds-controls--linear">
            <VProgressLinear indeterminate height="4" />
          </div>
          <span class="ds-spec">indeterminate</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">determinate</span>
          <div class="ds-controls ds-controls--linear">
            <VProgressLinear :model-value="progress" height="4" />
          </div>
          <span class="ds-spec">:model-value="{{ progress }}"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">buffer</span>
          <div class="ds-controls ds-controls--linear">
            <VProgressLinear :model-value="progress" :buffer-value="buffer" stream height="4" />
          </div>
          <span class="ds-spec">buffer={{ buffer }} · stream</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">heights</span>
          <div class="ds-controls ds-controls--linear">
            <VProgressLinear :model-value="progress" height="2" />
            <VProgressLinear :model-value="progress" height="4" />
            <VProgressLinear :model-value="progress" height="8" />
          </div>
          <span class="ds-spec">2 / 4 / 8 px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">striped</span>
          <div class="ds-controls ds-controls--linear">
            <VProgressLinear :model-value="progress" height="8" striped />
          </div>
          <span class="ds-spec">striped</span>
        </div>

      </div>
    </section>

    <!-- Custom .spin -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.loaders.spin') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <span class="spin" />
          </div>
          <span class="ds-spec">10×10px · accent</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">colors</span>
          <div class="ds-controls">
            <span class="spin spin--green" />
            <span class="spin spin--blue" />
          </div>
          <span class="ds-spec">green / blue</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">in context</span>
          <div class="ds-controls">
            <div class="spin-pill">
              <span class="spin" />
              <span>Processing...</span>
            </div>
            <div class="spin-pill spin-pill--blue">
              <span class="spin spin--blue" />
              <span>Loading</span>
            </div>
          </div>
          <span class="ds-spec">status pill</span>
        </div>

      </div>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--center { align-items: center; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  padding-top: 10px;
  .ds-row--center & { padding-top: 0; }
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  padding-top: 10px;
  .ds-row--center & { padding-top: 0; }
}

.ds-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;

  :deep(.v-progress-circular),
  :deep(.v-progress-circular__overlay),
  :deep(.v-progress-circular__underlay),
  :deep(.v-progress-circular svg) {
    overflow: visible;
  }
}

.ds-controls--linear {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-block: 4px;
  .v-progress-linear { width: 100%; }
}

.spin-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--accent-soft);
  border: 1px solid var(--accent-mid);
  border-radius: 5px;
  padding: 3px 8px;
  font-size: 11px;
  color: var(--accent);

  &--blue {
    background: var(--legacy-info-blue-10);
    border-color: var(--legacy-info-blue-25);
    color: var(--legacy-info-text);
  }
}
</style>
