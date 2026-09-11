<template>
  <div class="flex items-center gap-1.5">
    <Button
      v-if="!isTimingThis"
      variant="ghost"
      size="sm"
      :disabled="Boolean(activeTimer)"
      :title="
        activeTimer
          ? `Timer already running on ${activeTimer.subject}`
          : 'Start timing this task'
      "
      @click="start"
    >
      <template #prefix><LucidePlay class="size-3.5" /></template>
      Start
    </Button>

    <template v-else>
      <span
        class="rounded bg-surface-red-2 px-1.5 py-1 font-mono text-xs tabular-nums text-ink-red-3"
      >
        {{ elapsedLabel }}
      </span>
      <Button variant="ghost" size="sm" @click="showStop = true">
        <template #prefix><LucideSquare class="size-3.5" /></template>
        Stop
      </Button>
    </template>

    <StopTimerDialog v-model="showStop" :task="task" @logged="$emit('logged')" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button } from 'frappe-ui'
import StopTimerDialog from './StopTimerDialog.vue'
import { activeTimer, elapsedLabel, isTimingTask, startTimer } from '@/data/timer'

const props = defineProps({ task: { type: Object, required: true } })
defineEmits(['logged'])

const showStop = ref(false)
const isTimingThis = computed(() => isTimingTask(props.task?.name))

function start() {
  startTimer(props.task)
}
</script>
