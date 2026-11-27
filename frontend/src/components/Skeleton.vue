<template>
  <div class="animate-pulse rounded-4 bg-surface-gray-2" :class="className" :style="style" />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '0.75rem' },
  className: { type: String, default: '' },
})

const style = computed(() => ({ width: props.width, height: props.height }))
</script>
