<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconTag, IconCheck, IconUser } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'

const { t } = useI18n()

// Filter-group demo state: VChipGroup with multiple selection + `filter` prop.
const filters = ref<string[]>(['open'])
const filterOpts = ['open', 'closed', 'commercial', 'spam']

const closables = ref(['Design', 'Frontend', 'Vue'])
function removeTag(tag: string) {
  closables.value = closables.value.filter(x => x !== tag)
}

// Full color inventory for visual comparison — pick the standard palette from here.
// Theme colors = our tokens (vuetify.ts theme.light.colors); palette = Vuetify's
// built-in Material color names usable as `color="..."`.
const themeColors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
const paletteColors = [
  'red', 'pink', 'purple', 'deep-purple', 'indigo', 'blue', 'light-blue', 'cyan',
  'teal', 'green', 'light-green', 'lime', 'yellow', 'amber', 'orange', 'deep-orange',
  'brown', 'grey', 'blue-grey',
]
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.chips.title')" :description="t('design-system.page.chips.description')" back-to="/design-system" />

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.variants') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">tonal</span>
          <div class="ds-controls">
            <VChip color="primary" variant="tonal">Tonal</VChip>
            <VChip color="success" variant="tonal">Tonal</VChip>
            <VChip color="error" variant="tonal">Tonal</VChip>
          </div>
          <span class="ds-spec">variant="tonal" · default</span>
        </div>
        <div class="ds-row ds-row--center">
          <span class="ds-tag">flat</span>
          <div class="ds-controls">
            <VChip color="primary" variant="flat">Flat</VChip>
            <VChip color="success" variant="flat">Flat</VChip>
            <VChip color="error" variant="flat">Flat</VChip>
          </div>
          <span class="ds-spec">variant="flat" — solid fill</span>
        </div>
        <div class="ds-row ds-row--center">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VChip color="primary" variant="outlined">Outlined</VChip>
            <VChip color="success" variant="outlined">Outlined</VChip>
            <VChip color="error" variant="outlined">Outlined</VChip>
          </div>
          <span class="ds-spec">variant="outlined"</span>
        </div>
        <div class="ds-row ds-row--center">
          <span class="ds-tag">text</span>
          <div class="ds-controls">
            <VChip color="primary" variant="text">Text</VChip>
            <VChip color="success" variant="text">Text</VChip>
            <VChip color="error" variant="text">Text</VChip>
          </div>
          <span class="ds-spec">variant="text"</span>
        </div>
      </div>
    </section>

    <!-- Theme colors: tonal / flat / outlined side by side -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.theme') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VChip variant="tonal">default</VChip>
            <VChip variant="flat">default</VChip>
            <VChip variant="outlined">default</VChip>
          </div>
          <span class="ds-spec">no color</span>
        </div>
        <div v-for="c in themeColors" :key="c" class="ds-row ds-row--center">
          <span class="ds-tag">{{ c }}</span>
          <div class="ds-controls">
            <VChip :color="c" variant="tonal">{{ c }}</VChip>
            <VChip :color="c" variant="flat">{{ c }}</VChip>
            <VChip :color="c" variant="outlined">{{ c }}</VChip>
          </div>
          <span class="ds-spec">color="{{ c }}"</span>
        </div>
      </div>
    </section>

    <!-- Full Material palette: tonal / flat / outlined side by side -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.palette') }}</h6>
      <div class="ds-card">
        <div v-for="c in paletteColors" :key="c" class="ds-row ds-row--center">
          <span class="ds-tag">{{ c }}</span>
          <div class="ds-controls">
            <VChip :color="c" variant="tonal">{{ c }}</VChip>
            <VChip :color="c" variant="flat">{{ c }}</VChip>
            <VChip :color="c" variant="outlined">{{ c }}</VChip>
          </div>
          <span class="ds-spec">color="{{ c }}"</span>
        </div>
      </div>
    </section>

    <!-- Sizes -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.sizes') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">size</span>
          <div class="ds-controls">
            <VChip color="primary" variant="tonal" size="x-small">x-small</VChip>
            <VChip color="primary" variant="tonal" size="small">small</VChip>
            <VChip color="primary" variant="tonal">default</VChip>
            <VChip color="primary" variant="tonal" size="large">large</VChip>
            <VChip color="primary" variant="tonal" size="x-large">x-large</VChip>
          </div>
          <span class="ds-spec">x-small … x-large</span>
        </div>
      </div>
    </section>

    <!-- Content -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.content') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">icon</span>
          <div class="ds-controls">
            <VChip color="primary" variant="tonal" :prepend-icon="IconTag">prepend</VChip>
            <VChip color="success" variant="tonal" :append-icon="IconCheck">append</VChip>
          </div>
          <span class="ds-spec">prepend-icon · append-icon</span>
        </div>
        <div class="ds-row ds-row--center">
          <span class="ds-tag">avatar</span>
          <div class="ds-controls">
            <VChip color="primary" variant="tonal">
              <template #prepend>
                <VAvatar color="primary" size="20" class="me-1"><IconUser :size="14" /></VAvatar>
              </template>
              Вася
            </VChip>
          </div>
          <span class="ds-spec">#prepend → VAvatar</span>
        </div>
      </div>
    </section>

    <!-- Closable -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.closable') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">closable</span>
          <div class="ds-controls">
            <VChip
              v-for="tag in closables"
              :key="tag"
              color="primary"
              variant="tonal"
              size="small"
              closable
              @click:close="removeTag(tag)"
            >
              {{ tag }}
            </VChip>
            <span v-if="!closables.length" class="text-caption text-medium-emphasis">
              {{ t('design-system.section.chips.all_removed') }}
            </span>
          </div>
          <span class="ds-spec">closable · @click:close</span>
        </div>
      </div>
    </section>

    <!-- Filter group -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.filter') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">filter</span>
          <div class="ds-controls">
            <VChipGroup v-model="filters" multiple column>
              <VChip
                v-for="opt in filterOpts"
                :key="opt"
                :value="opt"
                color="primary"
                variant="tonal"
                size="small"
                filter
              >
                {{ opt }}
              </VChip>
            </VChipGroup>
          </div>
          <span class="ds-spec">VChipGroup · filter · multiple</span>
        </div>
      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.chips.states') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--center">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VChip color="primary" variant="tonal" disabled>Disabled</VChip>
            <VChip color="primary" variant="flat" disabled>Disabled</VChip>
          </div>
          <span class="ds-spec">disabled</span>
        </div>
        <div class="ds-row ds-row--center">
          <span class="ds-tag">link</span>
          <div class="ds-controls">
            <VChip color="primary" variant="tonal" link>Clickable</VChip>
          </div>
          <span class="ds-spec">link — hover/ripple</span>
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
</style>
