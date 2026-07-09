<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  IconRefresh, IconFilter, IconPlus, IconChevronUp, IconX,
  IconDeviceMobile, IconDeviceDesktop, IconGripVertical,
} from '@tabler/icons-vue'
import type { TablerIcon } from '@/shared/nav'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'

const { t } = useI18n()

// Preview viewport is SIMULATED via a fixed-width frame, independent of the real
// window — both layouts can be inspected without resizing the browser (the very
// pain this prototype is meant to design around).
const previewMobile = ref(true)

// A page contributes "actions". `placement` is the marking the prototype is
// about: on mobile, `bottom` actions relocate into the bottom action panel while
// `inline` ones stay in the page toolbar. `kind` decides the relocated form —
// a plain `button`, or a `panel` that opens a slide-up sheet (e.g. filters).
type Placement = 'inline' | 'bottom'
type Kind = 'button' | 'panel'
type ActionDef = { key: string; icon: TablerIcon; kind: Kind; placement: Placement }

const actions = ref<ActionDef[]>([
  { key: 'filters', icon: IconFilter, kind: 'panel', placement: 'bottom' },
  { key: 'refresh', icon: IconRefresh, kind: 'button', placement: 'bottom' },
  { key: 'create', icon: IconPlus, kind: 'button', placement: 'inline' },
])

// Which slide-up panel is open inside the mobile preview (null = none).
const openPanelKey = ref<string | null>(null)

// Desktop: everything inline. Mobile: only `inline`-marked actions stay up top.
const inlineActions = computed(() =>
  actions.value.filter(a => !previewMobile.value || a.placement === 'inline'),
)
// The bottom panel only exists in the mobile preview.
const bottomActions = computed(() =>
  previewMobile.value ? actions.value.filter(a => a.placement === 'bottom') : [],
)
// In desktop a `panel` action (filters) is shown expanded inline under the toolbar.
const inlinePanels = computed(() =>
  previewMobile.value ? [] : actions.value.filter(a => a.kind === 'panel'),
)

const openPanel = computed(() => actions.value.find(a => a.key === openPanelKey.value) ?? null)

function activate(a: ActionDef) {
  if (a.kind === 'panel') openPanelKey.value = openPanelKey.value === a.key ? null : a.key
}
function setPlacement(a: ActionDef, p: Placement) {
  a.placement = p
  if (p === 'inline' && openPanelKey.value === a.key) openPanelKey.value = null
}

const actionLabel = (key: string) => t(`design-system.section.action-panel.action.${key}`)
const placements: Placement[] = ['inline', 'bottom']
const placementLabel = (p: Placement) => t(`design-system.section.action-panel.placement.${p}`)
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.action-panel.title')"
        :description="t('design-system.page.action-panel.description')"
        back-to="/design-system"
      />

      <p class="ap-intro">{{ t('design-system.section.action-panel.intro') }}</p>

      <div class="ap-layout">
        <!-- ── Marking config ─────────────────────────────────── -->
        <section class="ds-section ap-config">
          <h6 class="mb-1">{{ t('design-system.section.action-panel.marking') }}</h6>
          <p class="ap-hint">{{ t('design-system.section.action-panel.markingHint') }}</p>

          <div class="ap-rows">
            <div v-for="a in actions" :key="a.key" class="ap-row">
              <IconGripVertical class="ap-row__grip" :size="16" :stroke-width="1.5" />
              <component :is="a.icon" class="ap-row__icon" :size="18" :stroke-width="1.5" />
              <span class="ap-row__label">{{ actionLabel(a.key) }}</span>
              <VBtnToggle
                :model-value="a.placement"
                density="compact"
                variant="outlined"
                divided
                mandatory
                class="ap-row__toggle"
                @update:model-value="setPlacement(a, $event)"
              >
                <VBtn v-for="p in placements" :key="p" :value="p" size="small">
                  {{ placementLabel(p) }}
                </VBtn>
              </VBtnToggle>
            </div>
          </div>

          <div class="ap-viewport">
            <span class="ap-viewport__label">{{ t('design-system.section.action-panel.viewport') }}</span>
            <VBtnToggle v-model="previewMobile" density="compact" variant="outlined" divided mandatory>
              <VBtn :value="false" size="small">
                <IconDeviceDesktop :size="16" class="mr-1" />
                {{ t('design-system.section.action-panel.desktop') }}
              </VBtn>
              <VBtn :value="true" size="small">
                <IconDeviceMobile :size="16" class="mr-1" />
                {{ t('design-system.section.action-panel.mobile') }}
              </VBtn>
            </VBtnToggle>
          </div>
        </section>

        <!-- ── Live preview frame ─────────────────────────────── -->
        <section class="ds-section ap-preview-wrap">
          <h6 class="mb-3">{{ t('design-system.section.action-panel.preview') }}</h6>

          <div class="ap-frame" :class="{ 'is-mobile': previewMobile }">
            <!-- Page toolbar: title + inline actions -->
            <div class="ap-toolbar">
              <span class="ap-toolbar__title">{{ t('design-system.section.action-panel.page.title') }}</span>
              <div class="ap-toolbar__actions">
                <VBtn
                  v-for="a in inlineActions"
                  :key="a.key"
                  :prepend-icon="a.icon"
                  variant="tonal"
                  size="small"
                  @click="activate(a)"
                >
                  {{ actionLabel(a.key) }}
                </VBtn>
              </div>
            </div>

            <!-- Desktop: panel actions (filters) expanded inline -->
            <div v-for="p in inlinePanels" :key="p.key" class="ap-filters">
              <VSelect
                :label="t('design-system.section.action-panel.filters.status')"
                :items="[]" density="compact" variant="outlined" hide-details
              />
              <VSelect
                :label="t('design-system.section.action-panel.filters.channel')"
                :items="[]" density="compact" variant="outlined" hide-details
              />
              <VTextField
                :label="t('design-system.section.action-panel.filters.search')"
                density="compact" variant="outlined" hide-details
              />
            </div>

            <!-- Fake page content -->
            <div class="ap-content">
              <div v-for="n in 5" :key="n" class="ap-content__row">
                <span class="ap-content__dot" />
                <span class="ap-content__bar" :style="{ width: 92 - n * 9 + '%' }" />
              </div>
            </div>

            <!-- Mobile: bottom action panel with the relocated actions -->
            <div v-if="bottomActions.length" class="ap-bottom">
              <button
                v-for="a in bottomActions"
                :key="a.key"
                type="button"
                class="ap-bottom__btn"
                :class="{ 'is-active': openPanelKey === a.key }"
                @click="activate(a)"
              >
                <component :is="a.icon" :size="20" :stroke-width="1.6" />
                <span>{{ actionLabel(a.key) }}</span>
              </button>
            </div>

            <!-- Mobile: slide-up sheet for an opened panel action -->
            <Transition name="ap-sheet">
              <div v-if="previewMobile && openPanel" class="ap-sheet">
                <div class="ap-sheet__head">
                  <IconChevronUp :size="16" class="ap-sheet__grip" />
                  <span class="ap-sheet__title">{{ actionLabel(openPanel.key) }}</span>
                  <VBtn :icon="IconX" variant="text" size="x-small" @click="openPanelKey = null" />
                </div>
                <div class="ap-sheet__body">
                  <VSelect
                    :label="t('design-system.section.action-panel.filters.status')"
                    :items="[]" density="compact" variant="outlined" hide-details
                  />
                  <VSelect
                    :label="t('design-system.section.action-panel.filters.channel')"
                    :items="[]" density="compact" variant="outlined" hide-details
                  />
                  <VTextField
                    :label="t('design-system.section.action-panel.filters.search')"
                    density="compact" variant="outlined" hide-details
                  />
                </div>
              </div>
            </Transition>
          </div>
        </section>
      </div>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 960px; }
.ds-section { margin-bottom: 24px; }

.ap-intro {
  margin: 0 0 20px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-muted);
  max-width: 760px;
}

.ap-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 24px;
  align-items: start;
}

@media (max-width: 959px) {
  .ap-layout { grid-template-columns: 1fr; }
}

/* ── Marking config ─────────────────────────────────────── */
.ap-hint {
  margin: 0 0 14px;
  font-size: 12px;
  color: var(--text-faint);
  line-height: 1.5;
}

.ap-rows { display: flex; flex-direction: column; gap: 8px; }

.ap-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  background: var(--surface);
}

.ap-row__grip { color: var(--text-faint); cursor: grab; flex-shrink: 0; }
.ap-row__icon { color: var(--accent); flex-shrink: 0; }
.ap-row__label { font-size: 13px; font-weight: 600; color: var(--text); flex: 1; }
.ap-row__toggle { flex-shrink: 0; }

.ap-viewport {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--border-soft);
}

.ap-viewport__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

/* ── Preview frame ──────────────────────────────────────── */
.ap-preview-wrap { display: flex; flex-direction: column; }

.ap-frame {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 460px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg);
  display: flex;
  flex-direction: column;
  transition: max-width 0.3s ease;
  margin: 0 auto;
}

.ap-frame.is-mobile {
  max-width: 380px;
}

.ap-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-soft);
  background: var(--surface);
}

.ap-toolbar__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ap-toolbar__actions { display: flex; gap: 8px; flex-shrink: 0; }

.ap-filters {
  display: grid;
  grid-template-columns: 1fr 1fr 1.4fr;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-soft);
}

.ap-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 14px;
}

.ap-content__row { display: flex; align-items: center; gap: 12px; }
.ap-content__dot {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--input-bg); flex-shrink: 0;
}
.ap-content__bar { height: 10px; border-radius: 5px; background: var(--input-bg); }

/* ── Bottom action panel (mobile) ───────────────────────── */
.ap-bottom {
  display: flex;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.ap-bottom__btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 9px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.ap-bottom__btn:hover { background: var(--surface-hover); color: var(--text); }
.ap-bottom__btn.is-active { color: var(--accent); background: var(--accent-soft); }

/* ── Slide-up sheet (mobile) ────────────────────────────── */
.ap-sheet {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  background: var(--surface);
  border-top: 1px solid var(--border);
  border-radius: var(--radius) var(--radius) 0 0;
  box-shadow: 0 -8px 24px rgb(0 0 0 / 18%);
  z-index: 2;
}

.ap-sheet__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px 8px 14px;
  border-bottom: 1px solid var(--border-soft);
}

.ap-sheet__grip { color: var(--text-faint); }
.ap-sheet__title { flex: 1; font-size: 13px; font-weight: 700; color: var(--text); }

.ap-sheet__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 14px;
}

.ap-sheet-enter-active, .ap-sheet-leave-active { transition: transform 0.25s ease, opacity 0.25s ease; }
.ap-sheet-enter-from, .ap-sheet-leave-to { transform: translateY(100%); opacity: 0; }
</style>
