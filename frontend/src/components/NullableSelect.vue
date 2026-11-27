<template>
  <!-- Select draws its own label in v1 (matching FormControl), and hugs its
       content unless told to fill the row -->
  <Select
    v-bind="$attrs"
    class="w-full"
    :label="label || undefined"
    :model-value="internalValue"
    :options="internalOptions"
    @update:model-value="onUpdate"
  />
</template>

<script setup>
import { computed } from 'vue'
import { Select } from 'frappe-ui'

/**
 * frappe-ui's Select drops any option whose value stringifies to "" -- see
 * `selectOptions` in Select.vue. That silently removes every "All types" /
 * "No type" entry, leaving no way to clear the field. This wrapper swaps the
 * empty value for a sentinel on the way in and back again on the way out, so
 * callers keep working with plain empty strings.
 */
const NONE = '__none__'

const props = defineProps({
  modelValue: { type: [String, Number, null], default: '' },
  options: { type: Array, default: () => [] },
  label: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const internalOptions = computed(() =>
  props.options.map((option) => {
    const normalised =
      typeof option === 'string' ? { label: option, value: option } : { ...option }
    if (normalised.value === '' || normalised.value == null) normalised.value = NONE
    return normalised
  }),
)

const internalValue = computed(() =>
  props.modelValue === '' || props.modelValue == null ? NONE : props.modelValue,
)

function onUpdate(value) {
  emit('update:modelValue', value === NONE ? '' : value)
}
</script>
