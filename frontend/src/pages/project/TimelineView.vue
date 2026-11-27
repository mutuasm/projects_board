<template>
  <div class="flex h-full flex-col">
    <EmptyState
      v-if="!scheduled.length"
      title="Nothing scheduled yet"
      description="Tasks appear here once they have an Expected Start or End Date."
    />

    <template v-else>
      <!-- toolbar -->
      <div class="flex shrink-0 items-center gap-2 border-b border-outline-gray-2 px-4 py-2 sm:px-6">
        <TabButtons
          v-model="groupBy"
          :options="[
            { label: 'By assignee', value: 'assignee' },
            { label: 'All tasks', value: 'none' },
          ]"
        />
        <Button variant="ghost" class="ml-auto" @click="scrollToToday(true)">
          <template #prefix><LucideLocateFixed class="size-4" /></template>
          Today
        </Button>
      </div>

      <div ref="scroller" class="thin-scrollbar min-h-0 flex-1 overflow-auto">
        <div class="relative min-h-full" :style="{ width: `${labelWidth + chartWidth}px` }">
          <!-- ruler: months over ISO weeks -->
          <div class="sticky top-0 z-20 flex border-b border-outline-gray-2 bg-surface-base">
            <div
              v-if="labelWidth"
              class="sticky left-0 z-30 shrink-0 border-r border-outline-gray-2 bg-surface-base"
              :style="{ width: `${labelWidth}px` }"
            />
            <div class="relative h-16" :style="{ width: `${chartWidth}px` }">
              <div
                v-for="month in months"
                :key="month.key"
                class="absolute top-0 flex h-8 items-end border-l border-outline-gray-2 pb-1"
                :style="{ left: `${month.offset * dayWidth}px`, width: `${month.days * dayWidth}px` }"
              >
                <span
                  class="sticky whitespace-nowrap px-2 text-sm-medium text-ink-gray-8"
                  :style="{ left: `${labelWidth}px` }"
                >
                  {{ month.label }}
                </span>
              </div>
              <div
                v-for="week in weeks"
                :key="week.key"
                class="absolute top-8 flex h-8 items-center gap-2 border-l border-outline-gray-2 px-2 text-xs"
                :class="week.current ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-5'"
                :style="{ left: `${week.offset * dayWidth}px`, width: `${7 * dayWidth}px` }"
              >
                <span class="font-medium">W{{ week.number }}</span>
                <span v-if="dayWidth * 7 > 90" class="truncate">{{ week.label }}</span>
              </div>
            </div>
          </div>

          <!-- grid lines and today, painted behind the lanes -->
          <div
            class="pointer-events-none absolute bottom-0 top-16"
            :style="{ left: `${labelWidth}px`, width: `${chartWidth}px` }"
          >
            <div
              v-for="week in weeks"
              :key="week.key"
              class="absolute inset-y-0 w-px bg-outline-gray-1"
              :style="{ left: `${week.offset * dayWidth}px` }"
            />
            <div
              v-if="todayOffset !== null"
              class="absolute inset-y-0 w-0.5 -translate-x-1/2 bg-red-500/70"
              :style="{ left: `${(todayOffset + 0.5) * dayWidth}px` }"
            >
              <span class="absolute -left-[3px] top-0 size-2 rounded-full bg-red-500" />
            </div>
          </div>

          <!-- lanes -->
          <div
            v-for="lane in lanes"
            :key="lane.key"
            class="flex border-b border-outline-gray-2"
          >
            <div
              v-if="labelWidth"
              class="sticky left-0 z-10 flex shrink-0 items-start gap-2.5 border-r border-outline-gray-2 bg-surface-base px-3 py-4 sm:px-5"
              :style="{ width: `${labelWidth}px` }"
            >
              <UserAvatar v-if="lane.user" :user="lane.user" size="lg" />
              <span
                v-else
                class="grid size-7 shrink-0 place-items-center rounded-full border border-dashed border-outline-gray-3 text-ink-gray-5"
              >
                <LucideUser class="size-3.5" />
              </span>
              <div class="min-w-0 pt-0.5">
                <p class="truncate text-sm-medium text-ink-gray-9">{{ lane.label }}</p>
                <p class="text-xs text-ink-gray-5">
                  {{ lane.cards.length }} {{ lane.cards.length === 1 ? 'task' : 'tasks' }}
                </p>
              </div>
            </div>

            <div class="relative" :style="{ width: `${chartWidth}px`, height: `${lane.height}px` }">
              <div
                v-for="card in lane.cards"
                :key="card.task.name"
                role="button"
                tabindex="0"
                class="pb-card absolute flex cursor-pointer flex-col justify-center gap-1.5 overflow-hidden !rounded-7 px-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                :style="{
                  left: `${card.left}px`,
                  width: `${card.width}px`,
                  top: `${card.row * ROW_HEIGHT + 8}px`,
                  height: `${ROW_HEIGHT - 12}px`,
                }"
                @click="openTask(card.task.name)"
                @keydown.enter="openTask(card.task.name)"
              >
                <div class="flex min-w-0 items-center gap-2">
                  <button
                    class="grid size-4 shrink-0 place-items-center rounded-4 border transition-colors"
                    :class="
                      card.task.status === 'Completed'
                        ? 'border-green-600 bg-green-600 text-white'
                        : 'border-outline-gray-4 hover:border-outline-gray-7'
                    "
                    :aria-label="card.task.status === 'Completed' ? 'Reopen task' : 'Mark complete'"
                    @click.stop="toggleComplete(card.task)"
                  >
                    <LucideCheck v-if="card.task.status === 'Completed'" class="size-3" />
                  </button>
                  <LucideFlag
                    v-if="card.task.is_milestone"
                    class="size-3.5 shrink-0 text-ink-amber-5"
                  />
                  <span
                    class="truncate text-sm-medium"
                    :class="
                      card.task.status === 'Completed'
                        ? 'text-ink-gray-5 line-through'
                        : 'text-ink-gray-9'
                    "
                  >
                    {{ card.task.subject }}
                  </span>
                </div>
                <div class="flex min-w-0 items-center gap-2 pl-6">
                  <AvatarStack :users="card.task.assignees || []" :max="2" size="xs" />
                  <span
                    class="truncate text-xs"
                    :class="isOverdue(card.task.exp_end_date, card.task.status) ? 'font-medium text-ink-red-5' : 'text-ink-gray-5'"
                  >
                    {{ card.dates }}
                  </span>
                </div>
                <!-- the real span, since a short task's card is wider than its dates -->
                <span
                  class="absolute bottom-0 left-0 h-[3px] rounded-full"
                  :class="barClass(card.task)"
                  :style="{ width: `${Math.min(card.span, card.width)}px` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { TabButtons, toast } from 'frappe-ui'
import AvatarStack from '@/components/AvatarStack.vue'
import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import api from '@/data/api'
import { upsertTask, visibleTasks } from '@/data/board'
import { isNarrow } from '@/data/ui'
import { dayjs, isOverdue } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

defineProps({ project: { type: String, required: true } })

const ROW_HEIGHT = 68
/** A card has to fit a title and a date line, whatever its real duration. */
const MIN_CARD = 240

const dayWidth = computed(() => (isNarrow.value ? 20 : 32))
const scroller = ref(null)

const groupBy = ref(readPref() || 'assignee')
const labelWidth = computed(() =>
  groupBy.value === 'assignee' ? (isNarrow.value ? 132 : 220) : 0,
)

function readPref() {
  try {
    return localStorage.getItem('pb:timeline-group')
  } catch {
    return null
  }
}
watch(groupBy, (value) => {
  try {
    localStorage.setItem('pb:timeline-group', value)
  } catch {
    // private mode: the choice just isn't remembered
  }
})

/** Only tasks with at least one date land on the timeline. */
const scheduled = computed(() =>
  visibleTasks.value
    .filter((t) => t.exp_start_date || t.exp_end_date)
    .map((t) => ({
      task: t,
      start: dayjs(t.exp_start_date || t.exp_end_date).startOf('day'),
      end: dayjs(t.exp_end_date || t.exp_start_date).startOf('day'),
    }))
    .sort((a, b) => a.start.valueOf() - b.start.valueOf()),
)

const startOfIsoWeek = (d) => d.subtract((d.day() + 6) % 7, 'day').startOf('day')

/** Whole weeks, Monday to Sunday, with a little air on both sides. */
const range = computed(() => {
  if (!scheduled.value.length) return null
  let min = scheduled.value[0].start
  let max = scheduled.value[0].end
  for (const item of scheduled.value) {
    if (item.start.isBefore(min)) min = item.start
    if (item.end.isAfter(max)) max = item.end
  }
  const today = dayjs().startOf('day')
  if (today.isBefore(min)) min = today
  if (today.isAfter(max)) max = today
  const start = startOfIsoWeek(min.subtract(7, 'day'))
  const end = startOfIsoWeek(max.add(14, 'day')).subtract(1, 'day')
  return { start, end }
})

const totalDays = computed(() =>
  range.value ? range.value.end.diff(range.value.start, 'day') + 1 : 0,
)
const chartWidth = computed(() => totalDays.value * dayWidth.value)

const months = computed(() => {
  if (!range.value) return []
  const out = []
  let cursor = range.value.start
  while (!cursor.isAfter(range.value.end)) {
    const endOfMonth = cursor.endOf('month').startOf('day')
    const last = endOfMonth.isAfter(range.value.end) ? range.value.end : endOfMonth
    out.push({
      key: cursor.format('YYYY-MM'),
      label: cursor.format('MMMM YYYY'),
      offset: cursor.diff(range.value.start, 'day'),
      days: last.diff(cursor, 'day') + 1,
    })
    cursor = last.add(1, 'day')
  }
  return out
})

function isoWeekNumber(d) {
  // the Thursday of a week decides which year's week it is
  const thursday = d.add(3 - ((d.day() + 6) % 7), 'day')
  return Math.floor(thursday.diff(thursday.startOf('year'), 'day') / 7) + 1
}

const weeks = computed(() => {
  if (!range.value) return []
  const out = []
  const thisWeek = startOfIsoWeek(dayjs())
  for (let d = range.value.start; !d.isAfter(range.value.end); d = d.add(7, 'day')) {
    const sunday = d.add(6, 'day')
    out.push({
      key: d.format('YYYY-MM-DD'),
      number: isoWeekNumber(d),
      label:
        d.month() === sunday.month()
          ? `${d.format('D')}–${sunday.format('D MMM')}`
          : `${d.format('D MMM')}–${sunday.format('D MMM')}`,
      offset: d.diff(range.value.start, 'day'),
      current: d.isSame(thisWeek, 'day'),
    })
  }
  return out
})

const todayOffset = computed(() => {
  if (!range.value) return null
  const offset = dayjs().startOf('day').diff(range.value.start, 'day')
  return offset >= 0 && offset < totalDays.value ? offset : null
})

function dateLabel(item) {
  if (item.start.isSame(item.end, 'day')) return item.end.format('D MMM, YYYY')
  const sameYear = item.start.year() === item.end.year()
  return `${item.start.format(sameYear ? 'D MMM' : 'D MMM YYYY')} → ${item.end.format('D MMM, YYYY')}`
}

/**
 * Place cards left to right, dropping each into the first row of its lane
 * where it no longer overlaps the previous card. Overlap is measured in
 * pixels, so a short task's minimum-width card never covers its neighbour.
 */
function pack(items) {
  const rowEnds = []
  const cards = items.map((item) => {
    const left = item.start.diff(range.value.start, 'day') * dayWidth.value + 3
    const span = (item.end.diff(item.start, 'day') + 1) * dayWidth.value - 6
    const width = Math.max(span, MIN_CARD)
    let row = rowEnds.findIndex((end) => end + 6 <= left)
    if (row === -1) row = rowEnds.length
    rowEnds[row] = left + width
    return { task: item.task, left, width, span, row, dates: dateLabel(item) }
  })
  return { cards, height: Math.max(rowEnds.length, 1) * ROW_HEIGHT + 4 }
}

const lanes = computed(() => {
  if (!range.value) return []
  if (groupBy.value !== 'assignee') {
    return [{ key: 'all', label: 'All tasks', user: null, ...pack(scheduled.value) }]
  }

  // a task shared by two people shows in both of their lanes
  const byUser = new Map()
  const unassigned = []
  for (const item of scheduled.value) {
    const people = item.task.assignees || []
    if (!people.length) unassigned.push(item)
    for (const person of people) {
      if (!byUser.has(person.name)) byUser.set(person.name, { user: person, items: [] })
      byUser.get(person.name).items.push(item)
    }
  }

  const out = [...byUser.values()]
    .sort((a, b) => (a.user.full_name || a.user.name).localeCompare(b.user.full_name || b.user.name))
    .map(({ user, items }) => ({
      key: user.name,
      label: user.full_name || user.name,
      user,
      ...pack(items),
    }))
  if (unassigned.length) {
    out.push({ key: '__unassigned', label: 'Unassigned', user: null, ...pack(unassigned) })
  }
  return out
})

function barClass(task) {
  if (task.status === 'Completed') return 'bg-green-500'
  if (task.status === 'Cancelled') return 'bg-gray-300'
  if (isOverdue(task.exp_end_date, task.status)) return 'bg-red-500'
  if (task.is_milestone) return 'bg-amber-500'
  return 'bg-blue-500'
}

async function toggleComplete(task) {
  const status = task.status === 'Completed' ? 'Open' : 'Completed'
  try {
    upsertTask(await api.moveTask(task.name, status))
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update the task')
  }
}

/** Open on this week rather than months of history. */
function scrollToToday(smooth = false) {
  const el = scroller.value
  if (!el || todayOffset.value === null) return
  const visible = el.clientWidth - labelWidth.value
  el.scrollTo({
    left: Math.max(todayOffset.value * dayWidth.value - visible / 4, 0),
    behavior: smooth ? 'smooth' : 'auto',
  })
}

watch(
  () => [scheduled.value.length > 0, dayWidth.value, groupBy.value],
  async ([hasTasks]) => {
    if (!hasTasks) return
    await nextTick()
    scrollToToday()
  },
  { immediate: true, flush: 'post' },
)
</script>
