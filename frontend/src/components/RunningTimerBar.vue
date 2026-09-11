<template>
  <!-- Persistent reminder that a timer is running, from anywhere in the app. -->
  <Transition
    enter-active-class="transition-all duration-200"
    leave-active-class="transition-all duration-150"
    enter-from-class="translate-y-4 opacity-0"
    leave-to-class="translate-y-4 opacity-0"
  >
    <div
      v-if="activeTimer"
      class="fixed bottom-4 left-1/2 z-30 flex -translate-x-1/2 items-center gap-3 rounded-full border border-outline-gray-3 bg-surface-white px-3 py-2 shadow-md"
      style="margin-bottom: env(safe-area-inset-bottom)"
    >
      <span class="relative flex size-2 shrink-0">
        <span
          class="absolute inline-flex size-full animate-ping rounded-full bg-red-400 opacity-75"
        />
        <span class="relative inline-flex size-2 rounded-full bg-red-500" />
      </span>

      <button
        class="min-w-0 max-w-40 truncate text-sm text-ink-gray-8 hover:underline sm:max-w-64"
        @click="openTask(activeTimer.task)"
      >
        {{ activeTimer.subject }}
      </button>

      <span class="font-mono text-sm tabular-nums text-ink-gray-9">
        {{ elapsedLabel }}
      </span>

      <Button variant="solid" size="sm" @click="showStop = true">
        <template #prefix><LucideSquare class="size-3.5" /></template>
        Stop
      </Button>
    </div>
  </Transition>

  <StopTimerDialog v-model="showStop" :task="activeTimer" />
</template>

<script setup>
import { ref } from 'vue'
import { Button } from 'frappe-ui'
import StopTimerDialog from './StopTimerDialog.vue'
import { activeTimer, elapsedLabel } from '@/data/timer'
import { openTask } from '@/utils/taskPanel'

const showStop = ref(false)
</script>
