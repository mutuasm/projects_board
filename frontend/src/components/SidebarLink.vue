<template>
  <router-link
    :to="to"
    class="flex items-center gap-2.5 rounded-lg border border-transparent px-2.5 py-2 text-[15px] text-ink-gray-7 transition-colors hover:bg-surface-gray-2"
    active-class="!border-outline-gray-2 !bg-surface-white font-medium !text-ink-gray-9 shadow-sm"
    :title="collapsed ? label : undefined"
  >
    <span class="shrink-0 text-ink-gray-7"><slot /></span>
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
