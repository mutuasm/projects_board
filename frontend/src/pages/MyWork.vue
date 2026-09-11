<template>
  <div class="flex h-full min-h-0 flex-col">
    <header class="shrink-0 border-b border-outline-gray-2 px-5 py-4">
      <div class="flex items-center gap-3">
        <div>
          <h1 class="text-xl font-semibold text-ink-gray-9">My work</h1>
          <p class="text-sm text-ink-gray-5">
            Every task assigned to you, across all projects.
          </p>
        </div>
        <div class="ml-auto flex items-center gap-2">
          <label class="flex items-center gap-1.5 text-sm text-ink-gray-6">
            <input
              v-model="includeCompleted"
              type="checkbox"
              class="rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
            />
            Show done
          </label>
          <Button variant="ghost" :loading="loading" @click="load">
            <template #prefix><LucideRefreshCw class="size-4" /></template>
            Refresh
          </Button>
        </div>
      </div>

      <!-- headline numbers, not a chart -->
      <div class="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="Assigned to me" :value="myTasks.length" />
        <StatTile
          label="Overdue"
          :value="buckets.overdue.length"
          :value-class="buckets.overdue.length ? 'text-ink-red-3' : 'text-ink-gray-9'"
        />
        <StatTile label="Due today" :value="buckets.today.length" />
        <StatTile label="In progress" :value="inProgressCount" />
      </div>
    </header>

    <div class="thin-scrollbar min-h-0 flex-1 overflow-y-auto px-5 py-4">
      <div v-if="loading && !myTasks.length" class="flex h-40 items-center justify-center">
        <LoadingIndicator class="size-5 text-ink-gray-5" />
      </div>

      <EmptyState
        v-else-if="!myTasks.length"
        title="Nothing on your plate"
        description="Tasks assigned to you show up here as soon as someone adds you."
      >
        <template #icon><LucideCheckCheck class="size-5 text-ink-gray-5" /></template>
        <Button class="mt-2" @click="$router.push({ name: 'Projects' })">
          Browse projects
        </Button>
      </EmptyState>

      <div v-else class="flex flex-col gap-5">
        <section v-for="bucket in orderedBuckets" :key="bucket.key">
          <h2 class="mb-2 flex items-center gap-2 text-sm font-semibold text-ink-gray-8">
            <component :is="bucket.icon" class="size-4" :class="bucket.iconClass" />
            {{ bucket.label }}
            <span class="text-xs font-normal tabular-nums text-ink-gray-5">
              {{ bucket.tasks.length }}
            </span>
          </h2>

          <ul class="overflow-hidden rounded-lg border border-outline-gray-2">
            <li
              v-for="task in bucket.tasks"
              :key="task.name"
              class="flex cursor-pointer items-center gap-3 border-b border-outline-gray-1 bg-surface-white px-3 py-2.5 last:border-b-0 hover:bg-surface-gray-1"
              @click="openTask(task.name)"
            >
              <PriorityIcon :priority="task.priority" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm text-ink-gray-8">{{ task.subject }}</p>
                <p class="truncate text-xs text-ink-gray-5">
                  {{ task.project_title || 'No project' }}
                  <span v-if="task.type"> · {{ task.type }}</span>
                </p>
              </div>
              <span
                v-if="task.exp_end_date"
                class="shrink-0 text-xs"
                :class="
                  isOverdue(task.exp_end_date, task.status)
                    ? 'font-medium text-ink-red-3'
                    : 'text-ink-gray-6'
                "
              >
                {{ dueLabel(task.exp_end_date) }}
              </span>
              <div class="shrink-0" @click.stop>
                <StatusPill :status="task.status" editable @change="(s) => move(task, s)" />
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Button, LoadingIndicator, toast } from 'frappe-ui'
import EmptyState from '@/components/EmptyState.vue'
import PriorityIcon from '@/components/PriorityIcon.vue'
import StatTile from '@/components/StatTile.vue'
import StatusPill from '@/components/StatusPill.vue'
import api from '@/data/api'
import { EVENTS, on } from '@/data/bus'
import { dayjs, dueLabel, isOverdue } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

import LucideAlarmClock from '~icons/lucide/alarm-clock'
import LucideCalendarDays from '~icons/lucide/calendar-days'
import LucideCalendarRange from '~icons/lucide/calendar-range'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideCircleDashed from '~icons/lucide/circle-dashed'

const myTasks = ref([])
const loading = ref(false)
const includeCompleted = ref(false)

async function load() {
  loading.value = true
  try {
    myTasks.value = (await api.getMyTasks(includeCompleted.value ? 1 : 0)) || []
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not load your tasks')
  } finally {
    loading.value = false
  }
}

const inProgressCount = computed(
  () => myTasks.value.filter((t) => t.status === 'Working').length,
)

/** Due-date buckets, the way a personal queue actually reads. */
const buckets = computed(() => {
  const out = { overdue: [], today: [], week: [], later: [], someday: [] }
  const endOfToday = dayjs().endOf('day')
  const endOfWeek = dayjs().add(7, 'day').endOf('day')

  for (const task of myTasks.value) {
    if (!task.exp_end_date) {
      out.someday.push(task)
      continue
    }
    const due = dayjs(task.exp_end_date)
    if (isOverdue(task.exp_end_date, task.status)) out.overdue.push(task)
    else if (due.isBefore(endOfToday)) out.today.push(task)
    else if (due.isBefore(endOfWeek)) out.week.push(task)
    else out.later.push(task)
  }
  return out
})

const orderedBuckets = computed(() =>
  [
    {
      key: 'overdue',
      label: 'Overdue',
      icon: LucideAlarmClock,
      iconClass: 'text-ink-red-3',
      tasks: buckets.value.overdue,
    },
    {
      key: 'today',
      label: 'Due today',
      icon: LucideCalendarDays,
      iconClass: 'text-ink-gray-6',
      tasks: buckets.value.today,
    },
    {
      key: 'week',
      label: 'Next 7 days',
      icon: LucideCalendarRange,
      iconClass: 'text-ink-gray-6',
      tasks: buckets.value.week,
    },
    {
      key: 'later',
      label: 'Later',
      icon: LucideCalendarClock,
      iconClass: 'text-ink-gray-6',
      tasks: buckets.value.later,
    },
    {
      key: 'someday',
      label: 'No due date',
      icon: LucideCircleDashed,
      iconClass: 'text-ink-gray-5',
      tasks: buckets.value.someday,
    },
  ].filter((bucket) => bucket.tasks.length),
)

async function move(task, status) {
  const previous = task.status
  task.status = status
  try {
    await api.moveTask(task.name, status)
    if (!includeCompleted.value && ['Completed', 'Cancelled'].includes(status)) {
      myTasks.value = myTasks.value.filter((t) => t.name !== task.name)
    }
  } catch (e) {
    task.status = previous
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update the task')
  }
}

watch(includeCompleted, load)

let unsubscribe = null
onMounted(() => {
  unsubscribe = on(EVENTS.TASK_UPDATED, load)
  load()
})
onUnmounted(() => unsubscribe?.())
</script>
