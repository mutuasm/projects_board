<template>
  <!--
    One row of a single-hue horizontal bar chart. Identity comes from the text
    label (plus an optional status dot), never from the bar colour, so the whole
    chart uses one validated hue and stays CVD-safe.
  -->
  <div class="flex items-center gap-2" :title="`${label}: ${value}`">
    <span
      v-if="dotClass"
      class="size-1.5 shrink-0 rounded-full"
      :class="dotClass"
    />
    <span class="w-20 shrink-0 truncate text-xs text-ink-gray-7 sm:w-28">
      {{ label }}
    </span>
    <div class="h-2 flex-1 overflow-hidden rounded-full bg-surface-gray-2">
      <div
        class="h-full rounded-full transition-all"
        :class="barClass"
        :style="{ width: `${percent}%` }"
      />
    </div>
    <span class="w-8 shrink-0 text-right text-xs tabular-nums text-ink-gray-7">
      {{ value }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  max: { type: Number, default: 1 },
  dotClass: { type: String, default: '' },
  barClass: { type: String, default: 'bg-surface-blue-6' },
})

const percent = computed(() =>
  props.max > 0 ? Math.max((props.value / props.max) * 100, props.value ? 3 : 0) : 0,
)
</script>
