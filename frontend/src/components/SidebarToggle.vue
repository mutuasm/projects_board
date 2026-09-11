<template>
  <button
    class="tap-target -ml-1 grid shrink-0 place-items-center rounded p-1.5 text-ink-gray-7 hover:bg-surface-gray-2 lg:hidden"
    aria-label="Open navigation"
    @click="openSidebar"
  >
    <LucideMenu class="size-5" />
  </button>
</template>

<script setup>
import { openSidebar } from '@/data/ui'
</script>
