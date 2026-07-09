<script setup lang="ts">
defineOptions({ inheritAttrs: false })

import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import {
  IconArrowLeft, IconArrowRight,
  IconBold, IconItalic, IconUnderline, IconStrikethrough,
  IconAlignLeft, IconAlignCenter, IconAlignRight,
  IconLayoutGrid, IconLayoutList,
  IconChevronLeft, IconChevronRight,
} from '@tabler/icons-vue'

// VBtnToggle — single
const period    = ref<string>('week')
const status    = ref<string>('all')
const viewMode  = ref<string>('grid')

// VBtnToggle — multiple
const format    = ref<string[]>([])
const align     = ref<string>('left')

// disabled item demo
const tab       = ref<string>('active')

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.button-group.title')" :description="t('design-system.page.button-group.description')" back-to="/design-system" />

    <!-- ── VBtnGroup ──────────────────────────────────────────── -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.button-group.neutral') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VBtnGroup variant="outlined" divided>
              <VBtn :prepend-icon="IconArrowLeft">Back</VBtn>
              <VBtn :append-icon="IconArrowRight">Next</VBtn>
            </VBtnGroup>
          </div>
          <span class="ds-spec">neutral navigation</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">tonal</span>
          <div class="ds-controls">
            <VBtnGroup variant="tonal" color="primary" divided>
              <VBtn :prepend-icon="IconArrowLeft">Back</VBtn>
              <VBtn :append-icon="IconArrowRight">Next</VBtn>
            </VBtnGroup>
          </div>
          <span class="ds-spec">with accent</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">icon-only</span>
          <div class="ds-controls">
            <VBtnGroup variant="outlined" divided>
              <VBtn :icon="IconChevronLeft" />
              <VBtn :icon="IconChevronRight" />
            </VBtnGroup>
            <VBtnGroup variant="tonal" color="primary" divided>
              <VBtn :icon="IconChevronLeft" />
              <VBtn :icon="IconChevronRight" />
            </VBtnGroup>
          </div>
          <span class="ds-spec">icons without text</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">density</span>
          <div class="ds-controls">
            <VBtnGroup variant="outlined" divided density="default">
              <VBtn :icon="IconChevronLeft" />
              <VBtn :icon="IconChevronRight" />
            </VBtnGroup>
            <VBtnGroup variant="outlined" divided density="comfortable">
              <VBtn :icon="IconChevronLeft" />
              <VBtn :icon="IconChevronRight" />
            </VBtnGroup>
            <VBtnGroup variant="outlined" divided density="compact">
              <VBtn :icon="IconChevronLeft" />
              <VBtn :icon="IconChevronRight" />
            </VBtnGroup>
          </div>
          <span class="ds-spec">default · comfortable · compact</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">size</span>
          <div class="ds-controls">
            <VBtnGroup variant="outlined" divided>
              <VBtn size="x-small" :icon="IconChevronLeft" />
              <VBtn size="x-small" :icon="IconChevronRight" />
            </VBtnGroup>
            <VBtnGroup variant="outlined" divided>
              <VBtn size="small" :icon="IconChevronLeft" />
              <VBtn size="small" :icon="IconChevronRight" />
            </VBtnGroup>
            <VBtnGroup variant="outlined" divided>
              <VBtn :icon="IconChevronLeft" />
              <VBtn :icon="IconChevronRight" />
            </VBtnGroup>
            <VBtnGroup variant="outlined" divided>
              <VBtn size="large" :icon="IconChevronLeft" />
              <VBtn size="large" :icon="IconChevronRight" />
            </VBtnGroup>
          </div>
          <span class="ds-spec">size on each VBtn — not inherited</span>
        </div>

      </div>
    </section>

    <!-- ── VBtnToggle — single ────────────────────────────────── -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.button-group.single') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">period</span>
          <div class="ds-controls">
            <VBtnToggle v-model="period" mandatory variant="outlined" divided>
              <VBtn value="day">Day</VBtn>
              <VBtn value="week">Week</VBtn>
              <VBtn value="month">Month</VBtn>
            </VBtnToggle>
            <span class="ds-val">{{ period }}</span>
          </div>
          <span class="ds-spec">size not set → default</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">status filter</span>
          <div class="ds-controls">
            <VBtnToggle v-model="status" mandatory variant="outlined" divided density="compact">
              <VBtn value="all"       size="small">All</VBtn>
              <VBtn value="active"    size="small">Active</VBtn>
              <VBtn value="done"      size="small">Done</VBtn>
              <VBtn value="failed"    size="small">Failed</VBtn>
            </VBtnToggle>
            <span class="ds-val">{{ status }}</span>
          </div>
          <span class="ds-spec">density=compact · size=small</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">view mode</span>
          <div class="ds-controls">
            <VBtnToggle v-model="viewMode" mandatory variant="outlined" divided density="compact">
              <VBtn value="grid" :icon="IconLayoutGrid" />
              <VBtn value="list" :icon="IconLayoutList" />
            </VBtnToggle>
            <span class="ds-val">{{ viewMode }}</span>
          </div>
          <span class="ds-spec">icons · view switcher</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">size</span>
          <div class="ds-controls">
            <VBtnToggle v-model="period" mandatory variant="outlined" divided>
              <VBtn size="x-small" value="day">Day</VBtn>
              <VBtn size="x-small" value="week">Week</VBtn>
              <VBtn size="x-small" value="month">Month</VBtn>
            </VBtnToggle>
            <VBtnToggle v-model="period" mandatory variant="outlined" divided>
              <VBtn size="small" value="day">Day</VBtn>
              <VBtn size="small" value="week">Week</VBtn>
              <VBtn size="small" value="month">Month</VBtn>
            </VBtnToggle>
            <VBtnToggle v-model="period" mandatory variant="outlined" divided>
              <VBtn value="day">Day</VBtn>
              <VBtn value="week">Week</VBtn>
              <VBtn value="month">Month</VBtn>
            </VBtnToggle>
            <VBtnToggle v-model="period" mandatory variant="outlined" divided>
              <VBtn size="large" value="day">Day</VBtn>
              <VBtn size="large" value="week">Week</VBtn>
              <VBtn size="large" value="month">Month</VBtn>
            </VBtnToggle>
          </div>
          <span class="ds-spec">x-small · small · default · large</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">with disabled</span>
          <div class="ds-controls">
            <VBtnToggle v-model="tab" mandatory variant="outlined" divided>
              <VBtn value="active">Active</VBtn>
              <VBtn value="archive" disabled>Archive</VBtn>
              <VBtn value="trash">Trash</VBtn>
            </VBtnToggle>
            <span class="ds-val">{{ tab }}</span>
          </div>
          <span class="ds-spec">disabled on a single button</span>
        </div>

      </div>
    </section>

    <!-- ── VBtnToggle — multiple ──────────────────────────────── -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.button-group.multiple') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">formatting</span>
          <div class="ds-controls">
            <VBtnToggle v-model="format" multiple variant="outlined" divided>
              <VBtn value="bold"          :icon="IconBold" />
              <VBtn value="italic"        :icon="IconItalic" />
              <VBtn value="underline"     :icon="IconUnderline" />
              <VBtn value="strikethrough" :icon="IconStrikethrough" />
            </VBtnToggle>
            <span class="ds-val">{{ format.length ? format.join(', ') : '—' }}</span>
          </div>
          <span class="ds-spec">multiple — icons</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">alignment</span>
          <div class="ds-controls">
            <VBtnToggle v-model="align" mandatory variant="outlined" divided>
              <VBtn value="left"   :icon="IconAlignLeft" />
              <VBtn value="center" :icon="IconAlignCenter" />
              <VBtn value="right"  :icon="IconAlignRight" />
            </VBtnToggle>
          </div>
          <span class="ds-spec">mandatory + icons</span>
        </div>

      </div>
    </section>

    <!-- ── Styling variants ───────────────────────────────────── -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.button-group.styling') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VBtnToggle v-model="period" mandatory variant="outlined" divided>
              <VBtn value="day">Day</VBtn>
              <VBtn value="week">Week</VBtn>
              <VBtn value="month">Month</VBtn>
            </VBtnToggle>
          </div>
          <span class="ds-spec">default</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">flat</span>
          <div class="ds-controls">
            <VBtnToggle v-model="period" mandatory variant="flat" divided>
              <VBtn value="day">Day</VBtn>
              <VBtn value="week">Week</VBtn>
              <VBtn value="month">Month</VBtn>
            </VBtnToggle>
          </div>
          <span class="ds-spec">no border</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">tonal</span>
          <div class="ds-controls">
            <VBtnToggle v-model="period" mandatory variant="tonal" color="primary" divided>
              <VBtn value="day">Day</VBtn>
              <VBtn value="week">Week</VBtn>
              <VBtn value="month">Month</VBtn>
            </VBtnToggle>
          </div>
          <span class="ds-spec">with color</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">rounded</span>
          <div class="ds-controls">
            <VBtnToggle v-model="period" mandatory variant="outlined" divided rounded="pill">
              <VBtn value="day">Day</VBtn>
              <VBtn value="week">Week</VBtn>
              <VBtn value="month">Month</VBtn>
            </VBtnToggle>
          </div>
          <span class="ds-spec">rounded=pill</span>
        </div>

      </div>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page    { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 120px 1fr 220px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
}

.ds-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.ds-val {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-soft);
  border-radius: 4px;
  padding: 2px 8px;
}
</style>
