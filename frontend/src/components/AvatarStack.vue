<template>
  <div v-if="users.length" class="flex items-center -space-x-1.5">
    <UserAvatar
      v-for="u in visible"
      :key="u.name"
      :user="u"
      :size="size"
      ring
    />
    <Tooltip v-if="overflow.length" :text="overflowNames">
      <div
        class="flex items-center justify-center rounded-full bg-surface-gray-3 text-ink-gray-7 ring-2 ring-surface-base"
        :class="overflowSizeClass"
      >
        +{{ overflow.length }}
      </div>
    </Tooltip>
  </div>
  <Tooltip v-else text="Unassigned">
    <div
      class="flex items-center justify-center rounded-full border border-dashed border-outline-gray-3 text-ink-gray-4"
      :class="overflowSizeClass"
    >
      <LucideUser class="size-3" />
    </div>
  </Tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({
  users: { type: Array, default: () => [] },
  max: { type: Number, default: 3 },
  size: { type: String, default: 'sm' },
})

const visible = computed(() => props.users.slice(0, props.max))
const overflow = computed(() => props.users.slice(props.max))
const overflowNames = computed(() =>
  overflow.value.map((u) => u.full_name || u.name).join(', '),
)
const overflowSizeClass = computed(() =>
  props.size === 'xs' ? 'size-5 text-[9px]' : 'size-6 text-[10px]',
)
</script>
