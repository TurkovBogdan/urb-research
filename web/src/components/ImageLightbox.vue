<script setup lang="ts">
/**
 * Full-screen preview of a single image, opened by clicking an image in chat content.
 * Driven by a v-model holding the image src — a non-empty src opens the dialog, closing
 * it clears the src. Clicking the backdrop, the image, or pressing Esc dismisses it.
 */
import { computed } from 'vue'

const props = defineProps<{ modelValue: string | null }>()
const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const open = computed({
  get: () => !!props.modelValue,
  set: (value) => {
    if (!value) emit('update:modelValue', null)
  },
})
</script>

<template>
  <VDialog v-model="open" max-width="92vw" :scrim="true" class="image-lightbox">
    <div class="image-lightbox__stage" @click="open = false">
      <img :src="modelValue ?? ''" alt="" class="image-lightbox__img" />
    </div>
  </VDialog>
</template>

<style scoped>
.image-lightbox__stage {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.image-lightbox__img {
  max-width: 92vw;
  max-height: 92vh;
  object-fit: contain;
  border-radius: 8px;
  /* Transparent PNGs would otherwise blend into the dark scrim — back them with white. */
  background: #fff;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.45);
}
</style>

<!-- The scrim is teleported outside this component, so it can't be reached from scoped
     styles; the dialog's `image-lightbox` class falls through to the overlay root. -->
<style>
.image-lightbox.v-overlay .v-overlay__scrim {
  background: #000 !important;
  opacity: 0.75;
}
</style>
