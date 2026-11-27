<template>
  <!-- frappe-ui's DatePicker with the app's defaults: a short date format,
       clearable, and a plain YYYY-MM-DD string either way -->
  <DatePicker
    :model-value="modelValue || ''"
    :label="label || undefined"
    :placeholder="placeholder"
    :variant="variant"
    :disabled="readonly"
    format="D MMM YYYY"
    clearable
    @update:model-value="(v) => $emit('update:modelValue', v || '')"
  />
</template>

<script setup>
import { DatePicker } from 'frappe-ui'

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: 'Pick a date' },
  variant: { type: String, default: 'subtle' },
  readonly: { type: Boolean, default: false },
})
defineEmits(['update:modelValue'])
</script>
