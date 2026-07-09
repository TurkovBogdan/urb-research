<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { IconSearch, IconUser, IconLock, IconMail, IconEye, IconEyeOff, IconCalendar } from '@tabler/icons-vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const v1  = ref('')
const v2  = ref('')
const v3  = ref('')
const v4  = ref('')
const v5  = ref('')
const v6  = ref('')
const v7  = ref('')
const v8  = ref('')
const v9  = ref('')
const v10 = ref('')
const v11 = ref('')
const v12 = ref<number | null>(null)
const v13 = ref('')
const v14 = ref('')
const v15 = ref('')
const v16 = ref('')

const showPwd = ref(false)

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.inputs.title')" :description="t('design-system.page.inputs.description')" back-to="/design-system" />

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.variants') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VTextField v-model="v1" label="Name" variant="outlined" hide-details />
          </div>
          <span class="ds-spec">primary</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">filled</span>
          <div class="ds-controls">
            <VTextField v-model="v2" label="Name" variant="filled" hide-details />
          </div>
          <span class="ds-spec">with background</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">plain</span>
          <div class="ds-controls">
            <VTextField v-model="v3" placeholder="Name" variant="plain" hide-details />
          </div>
          <span class="ds-spec">no border · placeholder</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">underlined</span>
          <div class="ds-controls">
            <VTextField v-model="v4" label="Name" variant="underlined" hide-details />
          </div>
          <span class="ds-spec">bottom line only</span>
        </div>

      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">clearable</span>
          <div class="ds-controls">
            <VTextField v-model="v5" label="Search" variant="outlined" clearable hide-details />
          </div>
          <span class="ds-spec">clearable</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">loading</span>
          <div class="ds-controls">
            <VTextField v-model="v6" label="Login" variant="outlined" loading hide-details />
          </div>
          <span class="ds-spec">loading</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">readonly</span>
          <div class="ds-controls">
            <VTextField label="Email" variant="outlined" model-value="user@example.com" readonly hide-details />
          </div>
          <span class="ds-spec">readonly</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VTextField label="Email" variant="outlined" model-value="user@example.com" disabled hide-details />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">error</span>
          <div class="ds-controls">
            <VTextField label="Email" variant="outlined" model-value="bad@" :error-messages="['Invalid email']" />
          </div>
          <span class="ds-spec">:error-messages</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">hint</span>
          <div class="ds-controls">
            <VTextField v-model="v7" label="Login" variant="outlined" hint="Latin letters, 3 characters minimum" persistent-hint />
          </div>
          <span class="ds-spec">hint + persistent-hint</span>
        </div>

      </div>
    </section>

    <!-- With icons -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.withIcons') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">prepend-inner</span>
          <div class="ds-controls">
            <VTextField v-model="v8" placeholder="Search" variant="outlined"
              :prepend-inner-icon="IconSearch" clearable hide-details />
          </div>
          <span class="ds-spec">:prepend-inner-icon</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">prepend</span>
          <div class="ds-controls">
            <VTextField v-model="v9" label="User" variant="outlined"
              :prepend-icon="IconUser" hide-details />
          </div>
          <span class="ds-spec">:prepend-icon</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">password</span>
          <div class="ds-controls">
            <VTextField v-model="v10" label="Password" variant="outlined"
              :prepend-inner-icon="IconLock"
              :type="showPwd ? 'text' : 'password'"
              :append-inner-icon="showPwd ? IconEyeOff : IconEye"
              @click:append-inner="showPwd = !showPwd"
              hide-details />
          </div>
          <span class="ds-spec">type=password + toggle</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">append-inner</span>
          <div class="ds-controls">
            <VTextField v-model="v11" label="Date" variant="outlined"
              :append-inner-icon="IconCalendar" hide-details />
          </div>
          <span class="ds-spec">:append-inner-icon</span>
        </div>

      </div>
    </section>

    <!-- Special types -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.specialTypes') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">number</span>
          <div class="ds-controls">
            <VTextField v-model.number="v12" label="Quantity" variant="outlined" type="number" hide-details />
          </div>
          <span class="ds-spec">type="number"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">prefix</span>
          <div class="ds-controls">
            <VTextField v-model="v13" label="Salary" variant="outlined" prefix="₽" hide-details />
          </div>
          <span class="ds-spec">prefix</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">suffix</span>
          <div class="ds-controls">
            <VTextField v-model="v14" label="Speed" variant="outlined" suffix="km/h" hide-details />
          </div>
          <span class="ds-spec">suffix</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">counter</span>
          <div class="ds-controls">
            <VTextField label="Description" variant="outlined" counter maxlength="100" />
          </div>
          <span class="ds-spec">counter + maxlength</span>
        </div>

      </div>
    </section>

    <!-- Textarea -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.multiline') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--start">
          <span class="ds-tag" style="padding-top: 10px">textarea</span>
          <div class="ds-controls">
            <VTextarea label="Cover letter" variant="outlined" rows="3" hide-details />
          </div>
          <span class="ds-spec" style="padding-top: 10px">VTextarea rows=3</span>
        </div>

        <div class="ds-row ds-row--start">
          <span class="ds-tag" style="padding-top: 10px">auto-grow</span>
          <div class="ds-controls">
            <VTextarea label="Comment" variant="outlined" auto-grow rows="2" hide-details />
          </div>
          <span class="ds-spec" style="padding-top: 10px">auto-grow</span>
        </div>

        <div class="ds-row ds-row--start">
          <span class="ds-tag" style="padding-top: 10px">no-resize</span>
          <div class="ds-controls">
            <VTextarea label="Note" variant="outlined" rows="3" no-resize hide-details />
          </div>
          <span class="ds-spec" style="padding-top: 10px">no-resize</span>
        </div>

      </div>
    </section>

    <!-- With description -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.description') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--start">
          <span class="ds-tag" style="padding-top: 10px">field</span>
          <div class="ds-controls">
            <VTextField v-model="v15" label="Display name" variant="outlined"
              hint="Shown to teammates across the workspace" persistent-hint />
          </div>
          <span class="ds-spec" style="padding-top: 10px">hint + persistent-hint</span>
        </div>

        <div class="ds-row ds-row--start">
          <span class="ds-tag" style="padding-top: 10px">textarea</span>
          <div class="ds-controls">
            <VTextarea v-model="v16" label="About" variant="outlined"
              hint="Role in the project, area of responsibility — briefly (up to 256 characters)"
              persistent-hint counter maxlength="256" rows="2" auto-grow />
          </div>
          <span class="ds-spec" style="padding-top: 10px">description + counter</span>
        </div>

      </div>
    </section>

    <!-- Density -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.inputs.density') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VTextField label="Field" variant="outlined" hide-details />
          </div>
          <span class="ds-spec">density="default"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">comfortable</span>
          <div class="ds-controls">
            <VTextField label="Field" variant="outlined" density="comfortable" hide-details />
          </div>
          <span class="ds-spec">density="comfortable"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">compact</span>
          <div class="ds-controls">
            <VTextField label="Field" variant="outlined" density="compact" hide-details />
          </div>
          <span class="ds-spec">density="compact"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">compact plain</span>
          <div class="ds-controls">
            <VTextField placeholder="Filter" variant="plain" density="compact" hide-details />
          </div>
          <span class="ds-spec">inline / filters</span>
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
  &.ds-row--start  { align-items: start; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  padding-top: 10px;
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  padding-top: 10px;
}

.ds-controls {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.v-text-field, .v-textarea {
  min-width: 220px;
  max-width: 320px;
}
</style>
