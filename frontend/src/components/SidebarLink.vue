<template>
  <router-link
    :to="to"
    class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
    active-class="bg-surface-gray-3 font-medium text-ink-gray-9"
    :title="collapsed ? label : undefined"
  >
    <span class="shrink-0 text-ink-gray-6"><slot /></span>
    <span v-if="!collapsed" class="truncate">{{ label }}</span>
  </router-link>
</template>

<script setup>
defineProps({
  to: { type: [String, Object], required: true },
  label: { type: String, required: true },
  collapsed: { type: Boolean, default: false },
})
</script>
