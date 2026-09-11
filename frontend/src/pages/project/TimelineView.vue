<template>
  <div class="flex h-full flex-col">
    <EmptyState
      v-if="!scheduled.length"
      title="Nothing scheduled yet"
      description="Tasks appear here once they have an Expected Start or End Date."
    />

    <div v-else class="flex min-h-0 flex-1">
      <!-- task names -->
      <div
        class="thin-scrollbar w-64 shrink-0 overflow-y-auto border-r border-outline-gray-2"
        ref="labelScroller"
        @scroll="syncScroll('labels')"
      >
        <div class="h-9 border-b border-outline-gray-2" />
        <div
          v-for="task in scheduled"
          :key="task.name"
          class="flex h-10 cursor-pointer items-center gap-2 border-b border-outline-gray-1 px-3 hover:bg-surface-gray-1"
          @click="openTask(task.name)"
        >
          <span class="size-1.5 shrink-0 rounded-full" :class="statusStyle(task.status).dot" />
          <span class="truncate text-sm text-ink-gray-8">{{ task.subject }}</span>
        </div>
      </div>

      <!-- chart -->
      <div
        class="thin-scrollbar min-w-0 flex-1 overflow-auto"
        ref="chartScroller"
        @scroll="syncScroll('chart')"
      >
        <div :style="{ width: `${totalDays * dayWidth}px` }">
          <!-- month ruler -->
          <div
            class="sticky top-0 z-10 flex h-9 border-b border-outline-gray-2 bg-surface-white"
          >
            <div
              v-for="month in months"
              :key="month.key"
              class="flex items-center border-r border-outline-gray-2 px-2 text-xs font-medium text-ink-gray-6"
              :style="{ width: `${month.days * dayWidth}px` }"
            >
              {{ month.label }}
            </div>
          </div>

          <div class="relative">
            <!-- today marker -->
            <div
              v-if="todayOffset !== null"
              class="pointer-events-none absolute top-0 z-10 h-full w-px bg-red-400"
              :style="{ left: `${todayOffset * dayWidth}px` }"
            />

            <div
              v-for="task in scheduled"
              :key="task.name"
              class="relative h-10 border-b border-outline-gray-1"
            >
              <Tooltip :text="tooltip(task)">
                <button
                  class="absolute top-2 h-6 rounded transition-opacity hover:opacity-80"
                  :class="barClass(task)"
                  :style="barStyle(task)"
                  @click="openTask(task.name)"
                >
                  <span
                    v-if="task.progress"
                    class="absolute inset-y-0 left-0 rounded-l bg-black/15"
                    :style="{ width: `${task.progress}%` }"
                  />
                  <span
                    class="relative px-2 text-xs font-medium text-ink-white"
                    >{{ task.subject }}</span
                  >
                </button>
              </Tooltip>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { Tooltip } from 'frappe-ui'
import EmptyState from '@/components/EmptyState.vue'
import { visibleTasks } from '@/data/board'
import { statusStyle } from '@/utils/constants'
import { dayjs, formatDate } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

defineProps({ project: { type: String, required: true } })

const dayWidth = 26
const labelScroller = ref(null)
const chartScroller = ref(null)
let syncing = false

/** Only tasks with at least one date land on the timeline. */
const scheduled = computed(() =>
  visibleTasks.value
    .filter((t) => t.exp_start_date || t.exp_end_date)
    .map((t) => ({
      ...t,
      _start: dayjs(t.exp_start_date || t.exp_end_date).startOf('day'),
      _end: dayjs(t.exp_end_date || t.exp_start_date).startOf('day'),
    }))
    .sort((a, b) => (a._start.isBefore(b._start) ? -1 : 1)),
)

const range = computed(() => {
  if (!scheduled.value.length) return null
  let min = scheduled.value[0]._start
  let max = scheduled.value[0]._end
  for (const task of scheduled.value) {
    if (task._start.isBefore(min)) min = task._start
    if (task._end.isAfter(max)) max = task._end
  }
  return { start: min.subtract(3, 'day'), end: max.add(3, 'day') }
})

const totalDays = computed(() =>
  range.value ? range.value.end.diff(range.value.start, 'day') + 1 : 0,
)

const months = computed(() => {
  if (!range.value) return []
  const out = []
  let cursor = range.value.start
  while (cursor.isBefore(range.value.end) || cursor.isSame(range.value.end, 'day')) {
    const endOfMonth = cursor.endOf('month')
    const last = endOfMonth.isAfter(range.value.end) ? range.value.end : endOfMonth
    out.push({
      key: cursor.format('YYYY-MM'),
      label: cursor.format('MMM YYYY'),
      days: last.diff(cursor, 'day') + 1,
    })
    cursor = last.add(1, 'day')
  }
  return out
})

const todayOffset = computed(() => {
  if (!range.value) return null
  const offset = dayjs().startOf('day').diff(range.value.start, 'day')
  return offset >= 0 && offset <= totalDays.value ? offset : null
})

function barStyle(task) {
  const offset = task._start.diff(range.value.start, 'day')
  const span = Math.max(task._end.diff(task._start, 'day') + 1, 1)
  return {
    left: `${offset * dayWidth}px`,
    width: `${span * dayWidth - 4}px`,
  }
}

function barClass(task) {
  if (task.status === 'Completed') return 'bg-green-600'
  if (task.status === 'Cancelled') return 'bg-gray-400'
  if (task.status === 'Overdue') return 'bg-red-500'
  if (task.is_milestone) return 'bg-amber-500'
  return 'bg-blue-500'
}

function tooltip(task) {
  const start = formatDate(task.exp_start_date)
  const end = formatDate(task.exp_end_date)
  return `${task.subject} · ${start || '?'} → ${end || '?'}`
}

/** Keep the label column and the chart rows lined up while scrolling. */
function syncScroll(source) {
  if (syncing) return
  syncing = true
  const from = source === 'labels' ? labelScroller.value : chartScroller.value
  const to = source === 'labels' ? chartScroller.value : labelScroller.value
  if (from && to) to.scrollTop = from.scrollTop
  nextTick(() => {
    syncing = false
  })
}
</script>
