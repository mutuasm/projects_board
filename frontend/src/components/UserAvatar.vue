<template>
  <Tooltip :text="tooltip" :hover-delay="0.3">
    <Avatar
      :image="user?.user_image"
      :label="user?.full_name || user?.name || 'Unassigned'"
      :size="size"
      :class="ringClass"
    />
  </Tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Tooltip } from 'frappe-ui'

const props = defineProps({
  user: { type: Object, default: () => ({}) },
  size: { type: String, default: 'sm' },
  ring: { type: Boolean, default: false },
})

const tooltip = computed(
  () => props.user?.full_name || props.user?.name || 'Unassigned',
)
const ringClass = computed(() =>
  props.ring ? 'ring-2 ring-surface-white rounded-full' : '',
)
</script>
