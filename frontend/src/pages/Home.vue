<template>
  <div class="flex h-full min-h-0 flex-col">
    <PageHeader title="Home">
      <template #actions>
        <Button v-if="permissions.canCreateTask" variant="solid" @click="openNewTask()">
          <template #prefix><LucidePlus class="size-4" /></template>
          <span class="hidden sm:inline">New task</span>
        </Button>
        <Dropdown :options="pageMenu" placement="right">
          <Button variant="ghost" label="More">
            <LucideMoreHorizontal class="size-4" />
          </Button>
        </Dropdown>
      </template>
    </PageHeader>

    <div class="thin-scrollbar min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto w-full max-w-[1072px] px-4 pb-12 pt-7 sm:px-8 sm:pt-10">
        <!-- greeting -->
        <h2 class="text-xl font-semibold tracking-tight text-ink-gray-9">
          {{ greeting }}, {{ firstName }}
        </h2>
        <p class="mt-1.5 text-base text-ink-gray-5">{{ summaryLine }}</p>

        <!-- today's brief -->
        <section class="mt-10 sm:mt-14">
          <div class="flex flex-wrap items-center gap-x-2 gap-y-3">
            <h3 class="text-lg font-semibold text-ink-gray-9">Today's brief</h3>
            <span class="text-base text-ink-gray-5">on</span>
            <Dropdown :options="projectMenu" placement="left">
              <button
                class="-ml-0.5 flex max-w-[16rem] items-center gap-1 rounded px-0.5 text-base text-ink-gray-8 hover:text-ink-gray-9"
              >
                <span class="truncate">{{ projectLabel }}</span>
                <LucideChevronDown class="size-3.5 shrink-0 text-ink-gray-5" />
              </button>
            </Dropdown>
            <TabButtons
              v-model="scope"
              class="ml-auto"
              :buttons="[
                { label: 'Team', value: 'team' },
                { label: 'For you', value: 'me' },
              ]"
            />
          </div>

          <div class="pb-panel mt-3 overflow-hidden">
            <!-- first load only; later refreshes keep the list on screen -->
            <div v-if="!brief" class="flex flex-col">
              <div v-for="n in 4" :key="n" class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-3 last:border-0">
                <div class="size-8 animate-pulse rounded-full bg-surface-gray-2" />
                <div class="flex flex-1 flex-col gap-1.5">
                  <div class="h-3 w-1/3 animate-pulse rounded bg-surface-gray-2" />
                  <div class="h-2.5 w-1/5 animate-pulse rounded bg-surface-gray-2" />
                </div>
              </div>
            </div>

            <div v-else-if="briefError" class="flex flex-col items-center gap-2 px-6 py-12 text-center">
              <p class="text-base text-ink-gray-7">Couldn't load the brief.</p>
              <Button size="sm" @click="loadBrief">Try again</Button>
            </div>

            <div
              v-else-if="!brief.items.length"
              class="flex flex-col items-center px-6 py-14 text-center"
            >
              <span class="grid size-10 place-items-center rounded-full bg-surface-gray-2">
                <LucideCheckCheck class="size-5 text-ink-gray-6" />
              </span>
              <p class="mt-4 text-base font-medium text-ink-gray-9">You're all caught up</p>
              <p class="mt-1 text-base text-ink-gray-5">
                {{
                  scope === 'me'
                    ? 'New assignments, reviews and due dates will show up here.'
                    : "Late, blocked and unassigned work across the team will show up here."
                }}
              </p>
            </div>

            <ul v-else>
              <li v-for="item in visibleItems" :key="`${item.kind}:${item.task}`">
                <button
                  class="flex w-full items-center gap-3 border-b border-outline-gray-1 px-4 py-3 text-left transition-colors hover:bg-surface-gray-1"
                  @click="openTask(item.task)"
                >
                  <span
                    class="grid size-8 shrink-0 place-items-center rounded-full"
                    :class="kindOf(item).bubble"
                  >
                    <component :is="kindOf(item).icon" class="size-4" />
                  </span>
                  <span class="min-w-0 flex-1">
                    <span class="flex min-w-0 items-baseline gap-2">
                      <span class="shrink-0 text-sm font-medium" :class="kindOf(item).text">
                        {{ kindOf(item).label }}
                      </span>
                      <span class="truncate text-base text-ink-gray-9">{{ item.subject }}</span>
                    </span>
                    <span class="mt-0.5 block truncate text-sm text-ink-gray-5">
                      {{ item.project_title }}
                      <template v-if="detailOf(item)"> · {{ detailOf(item) }}</template>
                    </span>
                  </span>
                  <AvatarStack
                    v-if="item.assignees.length"
                    :users="item.assignees"
                    :max="3"
                    class="hidden sm:flex"
                  />
                  <span
                    class="min-w-[5.5rem] shrink-0 whitespace-nowrap text-right text-sm tabular-nums"
                    :class="whenClass(item)"
                  >
                    {{ whenOf(item) }}
                  </span>
                </button>
              </li>
              <li v-if="hiddenCount" class="px-4 py-2.5">
                <button
                  class="text-sm font-medium text-ink-gray-6 hover:text-ink-gray-9"
                  @click="showAll = true"
                >
                  Show {{ hiddenCount }} more
                </button>
              </li>
            </ul>
          </div>
        </section>

        <!-- workload, and what is coming up -->
        <div class="mt-10 grid gap-5 sm:mt-14 lg:grid-cols-[minmax(0,1fr)_minmax(0,22rem)]">
          <section class="pb-panel flex min-w-0 flex-col p-5">
            <h3 class="text-lg font-semibold text-ink-gray-9">Team workload</h3>
            <p class="mt-1 flex flex-wrap items-center gap-x-1 text-base text-ink-gray-5">
              Open work now, and tasks done in
              <Dropdown :options="periodMenu" placement="left">
                <button class="flex items-center gap-1 text-ink-gray-8 hover:text-ink-gray-9">
                  {{ periodLabel }}
                  <LucideChevronDown class="size-3.5 text-ink-gray-5" />
                </button>
              </Dropdown>
            </p>

            <div class="thin-scrollbar -mx-1 mt-4 overflow-x-auto px-1">
              <div class="min-w-[560px]">
                <div
                  class="grid h-9 items-center gap-x-4 rounded-md bg-surface-gray-2 px-3 text-sm text-ink-gray-5"
                  :style="{ gridTemplateColumns: workloadColumns }"
                >
                  <span>Member</span>
                  <button
                    v-for="column in WORKLOAD_COLUMNS"
                    :key="column.key"
                    class="flex items-center justify-end gap-1 hover:text-ink-gray-8"
                    :class="sortKey === column.key && 'text-ink-gray-9'"
                    @click="sortBy(column.key)"
                  >
                    {{ column.label }}
                    <component
                      :is="sortDesc ? LucideArrowDown : LucideArrowUp"
                      v-if="sortKey === column.key"
                      class="size-3.5"
                    />
                  </button>
                </div>

                <template v-if="workload">
                  <div
                    v-for="member in sortedMembers"
                    :key="member.user.name"
                    class="grid items-center gap-x-4 border-b border-outline-gray-1 px-3 py-2.5 text-base last:border-0"
                    :style="{ gridTemplateColumns: workloadColumns }"
                  >
                    <span class="flex min-w-0 items-center gap-2">
                      <UserAvatar :user="member.user" size="sm" />
                      <span class="truncate text-ink-gray-8">
                        {{ member.user.full_name || member.user.name }}
                      </span>
                    </span>
                    <span
                      v-for="column in WORKLOAD_COLUMNS"
                      :key="column.key"
                      class="text-right tabular-nums"
                      :class="
                        column.key === 'overdue' && member.overdue
                          ? 'font-medium text-ink-red-4'
                          : member[column.key]
                            ? 'text-ink-gray-8'
                            : 'text-ink-gray-4'
                      "
                    >
                      {{ member[column.key] }}
                    </span>
                  </div>
                  <p
                    v-if="!sortedMembers.length"
                    class="px-3 py-10 text-center text-base text-ink-gray-5"
                  >
                    Nobody has open or finished work here yet.
                  </p>
                </template>
                <div v-else class="flex flex-col">
                  <div v-for="n in 3" :key="n" class="flex items-center gap-2 px-3 py-3">
                    <div class="size-6 animate-pulse rounded-full bg-surface-gray-2" />
                    <div class="h-3 w-32 animate-pulse rounded bg-surface-gray-2" />
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="pb-panel flex min-w-0 flex-col p-5">
            <div class="flex items-start gap-2">
              <div class="min-w-0 flex-1">
                <h3 class="text-lg font-semibold text-ink-gray-9">Milestones</h3>
                <p class="mt-1 text-base text-ink-gray-5">Next 30 days</p>
              </div>
              <Button
                v-if="permissions.canCreateTask"
                variant="ghost"
                label="New milestone"
                title="New milestone"
                @click="openNewTask({ milestone: true })"
              >
                <LucidePlus class="size-4" />
              </Button>
            </div>

            <ul v-if="milestones?.length" class="mt-3 flex flex-col">
              <li v-for="milestone in milestones" :key="milestone.name">
                <button
                  class="-mx-2 flex w-[calc(100%+1rem)] items-center gap-3 rounded-lg px-2 py-2 text-left hover:bg-surface-gray-1"
                  @click="openTask(milestone.name)"
                >
                  <span
                    class="flex w-11 shrink-0 flex-col items-center rounded-md py-1 leading-none"
                    :class="isLate(milestone) ? 'bg-surface-red-2 text-ink-red-4' : 'bg-surface-gray-2 text-ink-gray-7'"
                  >
                    <span class="text-[10px] font-medium uppercase">
                      {{ dayjs(milestone.exp_end_date).format('ddd') }}
                    </span>
                    <span class="mt-0.5 text-base font-semibold tabular-nums">
                      {{ dayjs(milestone.exp_end_date).format('D') }}
                    </span>
                  </span>
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-base text-ink-gray-9">{{ milestone.subject }}</span>
                    <span class="block truncate text-sm text-ink-gray-5">
                      {{ milestone.project_title }} · {{ dueText(milestone.exp_end_date) }}
                    </span>
                  </span>
                </button>
              </li>
            </ul>

            <div
              v-else-if="milestones"
              class="flex flex-1 flex-col items-center justify-center gap-3 py-12 text-center"
            >
              <LucideCalendarCheck class="size-6 text-ink-gray-5" />
              <p class="text-base text-ink-gray-6">No milestones coming up.</p>
            </div>
            <div v-else class="mt-3 flex flex-col gap-2">
              <div v-for="n in 3" :key="n" class="h-10 animate-pulse rounded-md bg-surface-gray-2" />
            </div>
          </section>
        </div>
      </div>
    </div>

    <CreateTaskDialog
      v-model="showNewTask"
      :project="project || null"
      :default-milestone="newMilestone"
      @created="refresh"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Button, Dropdown, TabButtons } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import AvatarStack from '@/components/AvatarStack.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import api from '@/data/api'
import { EVENTS, on } from '@/data/bus'
import { loadProjects, projects } from '@/data/projects'
import { batched, onListUpdate } from '@/data/realtime'
import { permissions, user } from '@/data/session'
import { dayjs, timeAgo } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

import LucideAlarmClock from '~icons/lucide/alarm-clock'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideEye from '~icons/lucide/eye'
import LucideUserPlus from '~icons/lucide/user-plus'
import LucideMessageSquare from '~icons/lucide/message-square'
import LucideLock from '~icons/lucide/lock'
import LucideUserX from '~icons/lucide/user-x'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideArrowDown from '~icons/lucide/arrow-down'
import LucideArrowUp from '~icons/lucide/arrow-up'

const BRIEF_LIMIT = 8

const KINDS = {
  overdue: { label: 'Overdue', icon: LucideAlarmClock, bubble: 'bg-surface-red-2 text-ink-red-4', text: 'text-ink-red-4' },
  due_today: { label: 'Due today', icon: LucideCalendarClock, bubble: 'bg-surface-amber-2 text-ink-amber-3', text: 'text-ink-amber-3' },
  review: { label: 'In review', icon: LucideEye, bubble: 'bg-surface-violet-1 text-ink-violet-1', text: 'text-ink-violet-1' },
  assigned: { label: 'Assigned to you', icon: LucideUserPlus, bubble: 'bg-surface-blue-2 text-ink-blue-3', text: 'text-ink-blue-3' },
  comment: { label: 'New comment', icon: LucideMessageSquare, bubble: 'bg-surface-cyan-1 text-ink-cyan-1', text: 'text-ink-cyan-1' },
  blocked: { label: 'Blocked', icon: LucideLock, bubble: 'bg-surface-orange-1 text-ink-amber-3', text: 'text-ink-amber-3' },
  unassigned: { label: 'Unassigned', icon: LucideUserX, bubble: 'bg-surface-gray-2 text-ink-gray-6', text: 'text-ink-gray-6' },
  done: { label: 'Done today', icon: LucideCircleCheck, bubble: 'bg-surface-green-2 text-ink-green-3', text: 'text-ink-green-3' },
}

const WORKLOAD_COLUMNS = [
  { key: 'open', label: 'Open' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'due_this_week', label: 'This week' },
  { key: 'in_review', label: 'In review' },
  { key: 'done', label: 'Done' },
]
const workloadColumns = 'minmax(0,2fr) repeat(5, minmax(0,1fr))'

function stored(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}
function store(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // private mode: the choice just isn't remembered
  }
}

const scope = ref(stored('pb:home-scope', 'me'))
const project = ref(stored('pb:home-project', ''))
const period = ref(stored('pb:home-period', 'last_month'))

const brief = ref(null)
const briefError = ref(false)
const workload = ref(null)
const milestones = ref(null)
const showAll = ref(false)
const showNewTask = ref(false)
const newMilestone = ref(false)

// --- greeting --------------------------------------------------------------

const firstName = computed(() => (user.value?.full_name || 'there').split(' ')[0])
const greeting = computed(() => {
  const hour = new Date().getHours()
  return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
})
const summaryLine = computed(() => {
  const n = brief.value?.needs_you
  if (n == null) return ' '
  if (!n) return 'Nothing needs you today'
  return `${n} ${n === 1 ? 'task needs' : 'tasks need'} you today`
})

// --- brief -----------------------------------------------------------------

const openProjects = computed(() => projects.value.filter((p) => p.status === 'Open'))

const projectLabel = computed(
  () => projects.value.find((p) => p.name === project.value)?.project_name || 'All projects',
)

const projectMenu = computed(() => [
  { label: 'All projects', onClick: () => (project.value = '') },
  ...openProjects.value.map((p) => ({ label: p.project_name, onClick: () => (project.value = p.name) })),
])

function kindOf(item) {
  const kind = KINDS[item.kind] || KINDS.unassigned
  if (item.kind === 'review' && scope.value === 'me') return { ...kind, label: 'Needs your review' }
  return kind
}

function actorName(item) {
  return item.actor?.full_name || item.actor?.name || ''
}

function detailOf(item) {
  if (item.kind === 'comment') return `${actorName(item)}: ${item.detail || ''}`
  if (item.kind === 'assigned' && item.actor) return `by ${actorName(item)}`
  if (item.kind === 'done' && item.actor) return `by ${actorName(item)}`
  if (item.kind === 'blocked') return 'waiting on another task'
  return ''
}

function dueText(value) {
  const days = dayjs(value).startOf('day').diff(dayjs().startOf('day'), 'day')
  if (days === 0) return 'today'
  if (days === 1) return 'tomorrow'
  if (days === -1) return '1 day late'
  return days < 0 ? `${-days} days late` : `in ${days} days`
}

function whenOf(item) {
  if (['comment', 'assigned', 'done'].includes(item.kind)) return timeAgo(item.when)
  if (item.exp_end_date) return dueText(item.exp_end_date)
  return ''
}

function whenClass(item) {
  return item.kind === 'overdue' ? 'text-ink-red-4' : 'text-ink-gray-5'
}

const visibleItems = computed(() => {
  const items = brief.value?.items || []
  return showAll.value ? items : items.slice(0, BRIEF_LIMIT)
})
const hiddenCount = computed(() => (brief.value?.items.length || 0) - visibleItems.value.length)

let briefRequest = 0
async function loadBrief() {
  const request = ++briefRequest
  briefError.value = false
  try {
    const data = await api.getBrief(scope.value, project.value)
    if (request === briefRequest) brief.value = data
  } catch {
    if (request === briefRequest) {
      briefError.value = true
      brief.value ??= { items: [], needs_you: null }
    }
  }
}

// --- workload --------------------------------------------------------------

const sortKey = ref('open')
const sortDesc = ref(true)

function sortBy(key) {
  if (sortKey.value === key) sortDesc.value = !sortDesc.value
  else {
    sortKey.value = key
    sortDesc.value = true
  }
}

const sortedMembers = computed(() => {
  const rows = [...(workload.value?.members || [])]
  const sign = sortDesc.value ? -1 : 1
  return rows.sort(
    (a, b) =>
      sign * (a[sortKey.value] - b[sortKey.value]) ||
      (a.user.full_name || '').localeCompare(b.user.full_name || ''),
  )
})

const periodLabel = computed(
  () => workload.value?.periods?.find((p) => p.value === period.value)?.label || 'Last month',
)
const periodMenu = computed(() =>
  (workload.value?.periods || [{ value: 'last_month', label: 'Last month' }]).map((p) => ({
    label: p.label,
    onClick: () => (period.value = p.value),
  })),
)

let workloadRequest = 0
async function loadWorkload() {
  const request = ++workloadRequest
  try {
    const data = await api.getTeamWorkload(period.value, project.value)
    if (request === workloadRequest) workload.value = data
  } catch {
    if (request === workloadRequest) workload.value ??= { members: [], periods: [] }
  }
}

// --- milestones ------------------------------------------------------------

function isLate(milestone) {
  return dayjs(milestone.exp_end_date).isBefore(dayjs(), 'day')
}

let milestonesRequest = 0
async function loadMilestones() {
  const request = ++milestonesRequest
  try {
    const rows = await api.getMilestones(project.value)
    if (request === milestonesRequest) milestones.value = rows || []
  } catch {
    if (request === milestonesRequest) milestones.value ??= []
  }
}

// --- page ------------------------------------------------------------------

function refresh() {
  loadBrief()
  loadWorkload()
  loadMilestones()
}

function openNewTask({ milestone = false } = {}) {
  newMilestone.value = milestone
  showNewTask.value = true
}

const pageMenu = [{ label: 'Refresh', icon: 'refresh-cw', onClick: refresh }]

watch(scope, (value) => {
  store('pb:home-scope', value)
  showAll.value = false
  loadBrief()
})
watch(project, (value) => {
  store('pb:home-project', value)
  showAll.value = false
  refresh()
})
watch(period, (value) => {
  store('pb:home-period', value)
  loadWorkload()
})

// a project picked last time may have been closed since
watch(projects, (list) => {
  if (project.value && list.length && !list.some((p) => p.name === project.value && p.status === 'Open'))
    project.value = ''
})

// edits in the task panel, and anyone else's, show up without a reload
const refreshLater = batched(refresh, 1500)
let stops = []
onMounted(() => {
  loadProjects()
  refresh()
  stops = [
    onListUpdate('Task', () => refreshLater()),
    on(EVENTS.TASK_UPDATED, () => refreshLater()),
    on(EVENTS.TASK_CREATED, () => refreshLater()),
    on(EVENTS.TASK_DELETED, () => refreshLater()),
  ]
})
onUnmounted(() => stops.forEach((stop) => stop?.()))
</script>
