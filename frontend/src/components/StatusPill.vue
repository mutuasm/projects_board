<template>
  <Dropdown v-if="editable" :options="statusOptions" placement="bottom-start">
    <button
      class="inline-flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium text-ink-gray-7 transition-colors hover:bg-surface-gray-2"
    >
      <span class="size-1.5 shrink-0 rounded-full" :class="style.dot" />
      {{ style.label || status }}
      <LucideChevronDown class="size-3 text-ink-gray-5" />
    </button>
  </Dropdown>
  <span
    v-else
    class="inline-flex items-center gap-1.5 text-xs font-medium text-ink-gray-7"
  >
    <span class="size-1.5 shrink-0 rounded-full" :class="style.dot" />
    {{ style.label || status }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { Dropdown } from 'frappe-ui'
import { statusStyle } from '@/utils/constants'
import { boardStatuses } from '@/data/session'

const props = defineProps({
  status: { type: String, default: 'Open' },
  editable: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

const style = computed(() => statusStyle(props.status))

const statusOptions = computed(() =>
  boardStatuses.value.map((s) => ({
    label: statusStyle(s).label || s,
    onClick: () => emit('change', s),
  })),
)
</script>
