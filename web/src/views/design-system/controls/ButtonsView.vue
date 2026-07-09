<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import {
  IconPlus, IconTrash, IconDownload, IconRefresh,
  IconPlayerPlay, IconSettings, IconArrowRight,
} from '@tabler/icons-vue'

const loading = ref(false)
const { t } = useI18n()

function triggerLoad() {
  loading.value = true
  setTimeout(() => { loading.value = false }, 1500)
}
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.buttons.title')" :description="t('design-system.page.buttons.description')" back-to="/design-system" />

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.buttons.variants') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">flat</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="flat">Primary</VBtn>
            <VBtn color="error"   variant="flat">Error</VBtn>
            <VBtn                 variant="flat">Default</VBtn>
          </div>
          <span class="ds-spec">primary action</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">tonal</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="tonal">Primary</VBtn>
            <VBtn color="error"   variant="tonal">Error</VBtn>
            <VBtn color="info"    variant="tonal">Info</VBtn>
          </div>
          <span class="ds-spec">secondary / soft accent</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VBtn variant="outlined">Default</VBtn>
            <VBtn color="error" variant="outlined">Error</VBtn>
            <VBtn color="primary" variant="outlined">Primary</VBtn>
          </div>
          <span class="ds-spec">neutral / destructive</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">text</span>
          <div class="ds-controls">
            <VBtn variant="text">Default</VBtn>
            <VBtn color="primary" variant="text">Primary</VBtn>
            <VBtn color="error"   variant="text">Error</VBtn>
          </div>
          <span class="ds-spec">inline, no background</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">plain</span>
          <div class="ds-controls">
            <VBtn variant="plain">Default</VBtn>
            <VBtn color="primary" variant="plain">Primary</VBtn>
          </div>
          <span class="ds-spec">minimal, no hover effect</span>
        </div>

      </div>
    </section>

    <!-- Icons -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.buttons.withIcons') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">prepend</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="flat" :prepend-icon="IconPlus">Add</VBtn>
            <VBtn variant="outlined" :prepend-icon="IconDownload">Export</VBtn>
            <VBtn variant="text" :prepend-icon="IconRefresh">Refresh</VBtn>
          </div>
          <span class="ds-spec">:prepend-icon</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">append</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="flat" :append-icon="IconArrowRight">Next</VBtn>
            <VBtn variant="text" :append-icon="IconArrowRight">Details</VBtn>
          </div>
          <span class="ds-spec">:append-icon</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">icon</span>
          <div class="ds-controls">
            <VBtn :icon="IconPlus"       variant="flat"     color="primary" />
            <VBtn :icon="IconTrash"      variant="outlined" color="error" />
            <VBtn :icon="IconSettings"   variant="text" />
            <VBtn :icon="IconPlayerPlay" variant="tonal"    color="primary" />
          </div>
          <span class="ds-spec">:icon — square button</span>
        </div>

      </div>
    </section>

    <!-- Sizes -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.buttons.sizes') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">x-small</span>
          <div class="ds-controls">
            <VBtn size="x-small" variant="flat" color="primary">X-Small</VBtn>
            <VBtn size="x-small" variant="outlined">X-Small</VBtn>
            <VBtn size="x-small" :icon="IconPlus" variant="tonal" color="primary" />
          </div>
          <span class="ds-spec">22px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">small</span>
          <div class="ds-controls">
            <VBtn size="small" variant="flat" color="primary">Small</VBtn>
            <VBtn size="small" variant="outlined">Small</VBtn>
            <VBtn size="small" :icon="IconPlus" variant="tonal" color="primary" />
          </div>
          <span class="ds-spec">26px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VBtn variant="flat" color="primary">Default</VBtn>
            <VBtn variant="outlined">Default</VBtn>
            <VBtn :icon="IconPlus" variant="tonal" color="primary" />
          </div>
          <span class="ds-spec">30px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">large</span>
          <div class="ds-controls">
            <VBtn size="large" variant="flat" color="primary">Large</VBtn>
            <VBtn size="large" variant="outlined">Large</VBtn>
            <VBtn size="large" :icon="IconPlus" variant="tonal" color="primary" />
          </div>
          <span class="ds-spec">36px</span>
        </div>

      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.buttons.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">loading</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="flat" :loading="loading" @click="triggerLoad">
              Save
            </VBtn>
            <VBtn color="primary" variant="tonal" :loading="loading" @click="triggerLoad">
              Apply
            </VBtn>
            <VBtn variant="outlined" :loading="loading" @click="triggerLoad">
              Export
            </VBtn>
            <VBtn variant="text" :loading="loading" @click="triggerLoad">
              Cancel
            </VBtn>
          </div>
          <span class="ds-spec">:loading — spinner replaces text</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">loading + icon</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="flat" :loading="loading" :prepend-icon="IconDownload" @click="triggerLoad">
              Download
            </VBtn>
            <VBtn variant="outlined" :loading="loading" :prepend-icon="IconPlus" @click="triggerLoad">
              Add
            </VBtn>
            <VBtn variant="text" :loading="loading" :prepend-icon="IconRefresh" @click="triggerLoad">
              Refresh
            </VBtn>
          </div>
          <span class="ds-spec">prepend-icon hidden behind the spinner</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">loading icon-only</span>
          <div class="ds-controls">
            <VBtn :icon="IconRefresh" variant="text" :loading="loading" @click="triggerLoad" />
            <VBtn :icon="IconPlus" variant="tonal" color="primary" :loading="loading" @click="triggerLoad" />
            <VBtn :icon="IconTrash" variant="outlined" color="error" :loading="loading" @click="triggerLoad" />
          </div>
          <span class="ds-spec">square buttons — spinner centered</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">spinning icon</span>
          <div class="ds-controls">
            <VBtn variant="text" :disabled="loading" @click="triggerLoad">
              <template #prepend>
                <IconRefresh :size="16" :class="{ 'icon-spin': loading }" />
              </template>
              Refresh
            </VBtn>
          </div>
          <span class="ds-spec">refresh only — icon spins, text stays put</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VBtn color="primary" variant="flat" disabled>Primary</VBtn>
            <VBtn variant="outlined" disabled>Outlined</VBtn>
            <VBtn variant="text" disabled>Text</VBtn>
            <VBtn :icon="IconPlus" variant="tonal" color="primary" disabled />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

      </div>
    </section>

    <!-- Loading guide -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.buttons.whenToUse') }}</h6>
      <div class="ds-card">
        <div class="ds-rule">
          <code class="ds-rule__code">:loading</code>
          <p class="ds-rule__text">
            Default for any action button (Save, Apply, Download, Sync, Add).
            The spinner replaces the content, clicks are blocked, and the width is preserved.
          </p>
        </div>
        <div class="ds-rule">
          <code class="ds-rule__code">icon-spin</code>
          <p class="ds-rule__text">
            Only for refresh buttons, where a spinning icon carries the "refreshing" semantics.
            The icon spins while the text stays readable. Don't use it elsewhere —
            a spinning cloud or a spinning plus looks odd.
          </p>
        </div>
      </div>
    </section>


  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page {
  max-width: 860px;
}

.ds-section {
  margin-bottom: 28px;
}

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  align-items: center;
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

.ds-rule {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 16px;
  align-items: baseline;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
}

.ds-rule__code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  background: var(--surface-hi);
  border: 1px solid var(--border-soft);
  border-radius: 4px;
  padding: 2px 6px;
  width: fit-content;
}

.ds-rule__text {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
