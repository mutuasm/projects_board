<template>
  <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-3">
    <div class="flex items-center gap-1.5">
      <slot name="icon" />
      <p class="text-xs font-medium text-ink-gray-5">{{ label }}</p>
    </div>
    <p class="mt-1.5 text-2xl font-semibold tabular-nums" :class="valueClass">
      {{ value }}
    </p>
    <p v-if="sub" class="mt-0.5 text-xs text-ink-gray-5">{{ sub }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  sub: { type: String, default: '' },
  valueClass: { type: String, default: 'text-ink-gray-9' },
})
</script>
