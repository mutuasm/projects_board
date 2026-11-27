<template>
  <Dropdown v-if="editable" :options="priorityOptions">
    <button
      class="inline-flex items-center gap-1 rounded-4 px-1.5 py-1 text-xs-medium hover:bg-surface-gray-2"
      :class="style.text"
    >
      <Icon :icon="style.icon" class="size-3.5" />
      <span v-if="showLabel">{{ priority || 'Unset' }}</span>
    </button>
  </Dropdown>
  <Tooltip v-else :text="`Priority: ${priority || 'Unset'}`">
    <span class="inline-flex items-center gap-1 text-xs-medium" :class="style.text">
      <Icon :icon="style.icon" class="size-3.5" />
      <span v-if="showLabel">{{ priority || 'Unset' }}</span>
    </span>
  </Tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { Dropdown, Icon, Tooltip } from 'frappe-ui'
import { priorityStyle } from '@/utils/constants'
import { taskPriorities } from '@/data/session'

const props = defineProps({
  priority: { type: String, default: 'Medium' },
  editable: { type: Boolean, default: false },
  showLabel: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

const style = computed(() => priorityStyle(props.priority))
const priorityOptions = computed(() =>
  taskPriorities.value.map((p) => ({ label: p, onClick: () => emit('change', p) })),
)
</script>
