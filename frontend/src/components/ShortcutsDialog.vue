<template>
  <Dialog v-model="show" :options="{ title: 'Keyboard shortcuts', size: 'md' }">
    <template #body-content>
      <dl class="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-2.5 text-sm">
        <template v-for="row in shortcuts" :key="row.label">
          <dt class="flex gap-1">
            <kbd
              v-for="key in row.keys"
              :key="key"
              class="rounded border border-outline-gray-2 bg-surface-gray-1 px-1.5 py-0.5 font-mono text-xs text-ink-gray-7"
            >
              {{ key }}
            </kbd>
          </dt>
          <dd class="text-ink-gray-7">{{ row.label }}</dd>
        </template>
      </dl>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Dialog } from 'frappe-ui'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const shortcuts = [
  { keys: ['⌘', 'K'], label: 'Open the command palette' },
  { keys: ['/'], label: 'Focus search' },
  { keys: ['C'], label: 'Create a task' },
  { keys: ['G', 'W'], label: 'Go to My Work' },
  { keys: ['G', 'P'], label: 'Go to Projects' },
  { keys: ['Esc'], label: 'Close the panel or dialog' },
  { keys: ['?'], label: 'Show this list' },
]
</script>
