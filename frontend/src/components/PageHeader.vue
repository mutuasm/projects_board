<template>
  <!-- the bar across the top of every page, as in Frappe CRM: where you are on
       the left, what you can do here on the right -->
  <header
    class="flex h-12 shrink-0 items-center gap-2 border-b border-outline-gray-2 px-3 pt-safe-top sm:px-5"
  >
    <SidebarToggle />
    <div class="flex min-w-0 flex-1 items-center gap-1.5 text-lg text-ink-gray-9">
      <slot name="title">
        <h1 class="truncate font-medium">{{ title }}</h1>
      </slot>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
import SidebarToggle from './SidebarToggle.vue'

defineProps({ title: { type: String, default: '' } })
</script>
