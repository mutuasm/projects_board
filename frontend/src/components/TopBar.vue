<template>
  <div class="shrink-0 border-b border-outline-gray-2 px-4 pt-safe-top sm:px-5">
    <div class="flex h-14 items-center gap-2 short:h-11">
      <SidebarToggle />

      <!-- the palette already searches projects, views and tasks; this is its front door -->
      <button
        class="flex h-9 min-w-0 flex-1 items-center gap-2.5 rounded-lg bg-surface-gray-2 px-3 text-left text-sm text-ink-gray-5 transition-colors hover:bg-surface-gray-3 sm:max-w-xl"
        @click="paletteOpen = true"
      >
        <LucideSearch class="size-4 shrink-0 text-ink-gray-6" />
        <span class="truncate">Search or type a command</span>
        <kbd
          class="ml-auto hidden shrink-0 rounded border border-outline-gray-2 bg-surface-white px-1.5 font-sans text-[11px] text-ink-gray-5 sm:inline"
        >
          {{ shortcut }}
        </kbd>
      </button>

      <NotificationsBell class="ml-auto" />

      <a
        href="/app"
        class="flex h-9 shrink-0 items-center gap-1.5 rounded-lg border border-outline-gray-2 px-3 text-sm font-medium text-ink-gray-8 transition-colors hover:bg-surface-gray-2"
        title="Go to the ERPNext desk"
      >
        <LucideMonitor class="size-4 text-ink-gray-6" />
        <span class="hidden sm:inline">Desk</span>
        <LucideArrowUpRight class="hidden size-3.5 text-ink-gray-5 sm:block" />
      </a>
    </div>
  </div>
</template>

<script setup>
import NotificationsBell from './NotificationsBell.vue'
import SidebarToggle from './SidebarToggle.vue'
import { paletteOpen } from '@/composables/useShortcuts'

const shortcut = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘K' : 'Ctrl K'
</script>
