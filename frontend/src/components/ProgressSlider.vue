<template>
  <div class="flex w-full items-center gap-2">
    <input
      :value="modelValue"
      type="range"
      min="0"
      max="100"
      :step="step"
      :disabled="disabled"
      :aria-label="`Progress: ${modelValue}%`"
      class="pb-range min-w-0 flex-1"
      :style="{ '--pb-range-fill': `${modelValue}%` }"
      @input="$emit('update:modelValue', Number($event.target.value))"
      @change="$emit('commit', Number($event.target.value))"
    />
    <span class="w-9 shrink-0 text-right text-xs tabular-nums text-ink-gray-7">
      {{ modelValue }}%
    </span>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: Number, default: 0 },
  step: { type: Number, default: 5 },
  disabled: { type: Boolean, default: false },
})
defineEmits(['update:modelValue', 'commit'])
</script>
