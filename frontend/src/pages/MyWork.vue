<template>
  <div class="thin-scrollbar h-full overflow-y-auto">
    <div class="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-5 pb-safe-bottom sm:px-6 sm:py-6">
      <!-- greeting -->
      <header class="flex flex-wrap items-end gap-x-3 gap-y-3">
        <div class="min-w-0">
          <p class="text-sm text-ink-gray-5">{{ todayLabel }}</p>
          <h1
            class="mt-0.5 truncate text-xl font-semibold tracking-tight text-ink-gray-9 sm:text-[26px] sm:leading-9"
          >
            {{ greeting }}, {{ firstName }}
          </h1>
          <p class="mt-0.5 text-sm text-ink-gray-6">{{ summaryLine }}</p>
        </div>
        <div class="flex w-full shrink-0 items-center gap-2 sm:ml-auto sm:w-auto">
          <Button
            v-if="permissions.canCreateProject"
            class="flex-1 sm:flex-none"
            @click="showNewProject = true"
          >
            <template #prefix><LucideFolderPlus class="size-4" /></template>
            New project
          </Button>
          <Button
            v-if="permissions.canCreateTask"
            variant="solid"
            class="flex-1 sm:flex-none"
            @click="showNewTask = true"
          >
            <template #prefix><LucidePlus class="size-4" /></template>
            New task
          </Button>
        </div>
      </header>

      <!-- headline numbers -->
      <div class="grid grid-cols-2 gap-2 sm:gap-3 md:grid-cols-4">
        <StatTile label="Open tasks" :value="active.length">
          <template #icon><LucideListTodo class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
        <StatTile
          label="Overdue"
          :value="buckets.overdue.length"
          :value-class="buckets.overdue.length ? 'text-ink-red-3' : 'text-ink-gray-9'"
        >
          <template #icon><LucideAlarmClock class="size-3.5 text-ink-red-3" /></template>
        </StatTile>
        <StatTile label="Due in 7 days" :value="buckets.today.length + buckets.week.length">
          <template #icon><LucideCalendarRange class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
        <StatTile label="Completed, last 14 days" :value="recentlyCompleted.length">
          <template #icon><LucideCheckCheck class="size-3.5 text-ink-green-3" /></template>
        </StatTile>
      </div>

      <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <!-- the queue -->
        <section class="min-w-0">
          <!-- sign-offs: tasks you handed out that are now waiting in review -->
          <section v-if="reviews.length" class="mb-6">
            <h2 class="mb-2 flex items-center gap-2 text-sm font-semibold text-ink-gray-8">
              <LucideClipboardCheck class="size-4 text-ink-amber-3" />
              Waiting on your review
              <span class="text-xs font-normal tabular-nums text-ink-gray-5">
                {{ reviews.length }}
              </span>
            </h2>
            <ul class="pb-panel overflow-hidden">
              <li
                v-for="task in reviews"
                :key="task.name"
                class="flex cursor-pointer flex-wrap items-center gap-3 border-b border-outline-gray-1 bg-surface-white px-3 py-3 last:border-b-0 hover:bg-surface-gray-1"
                @click="openTask(task.name)"
              >
                <AvatarStack :users="task.assignees || []" :max="2" size="sm" />
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm text-ink-gray-9">{{ task.subject }}</p>
                  <p class="flex items-center gap-1.5 truncate text-xs text-ink-gray-5">
                    <span
                      v-if="task.project"
                      class="size-2 shrink-0 rounded-[3px]"
                      :style="{ backgroundColor: projectColor(task.project) }"
                    />
                    {{ task.project_title || 'No project' }}
                    <template v-if="task.review_date">
                      ·
                      <span :class="reviewLate(task) ? 'font-medium text-ink-red-3' : ''">
                        review by {{ dueLabel(task.review_date) }}
                      </span>
                    </template>
                  </p>
                </div>
                <div class="flex shrink-0 gap-2" @click.stop>
                  <Button size="sm" :loading="reviewing === task.name" @click="signOff(task, 'Working')">
                    Send back
                  </Button>
                  <Button
                    size="sm"
                    variant="solid"
                    :loading="reviewing === task.name"
                    @click="signOff(task, 'Completed')"
                  >
                    Approve
                  </Button>
                </div>
              </li>
            </ul>
          </section>

          <div class="mb-3 flex flex-wrap items-center gap-2">
            <div class="relative min-w-0 basis-full sm:max-w-xs sm:flex-1 sm:basis-auto">
              <LucideSearch
                class="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-ink-gray-5"
              />
              <input
                v-model="search"
                type="search"
                placeholder="Filter my tasks"
                class="pb-input h-8 w-full pl-8 pr-2 text-sm"
              />
            </div>
            <TabButtons
              v-model="groupBy"
              :buttons="[
                { label: 'Due date', value: 'due' },
                { label: 'Project', value: 'project' },
                { label: 'Status', value: 'status' },
              ]"
            />
            <label class="ml-auto flex items-center gap-1.5 text-sm text-ink-gray-6">
              <input
                v-model="includeCompleted"
                type="checkbox"
                class="rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
              />
              Show done
            </label>
            <Tooltip text="Refresh">
              <Button variant="ghost" :loading="loading" aria-label="Refresh" @click="load">
                <LucideRefreshCw class="size-4" />
              </Button>
            </Tooltip>
          </div>

          <div v-if="loading && !myTasks.length" class="flex h-40 items-center justify-center">
            <LoadingIndicator class="size-5 text-ink-gray-5" />
          </div>

          <EmptyState
            v-else-if="!active.length && !includeCompleted"
            title="Nothing on your plate"
            description="Tasks assigned to you show up here as soon as someone adds you - including tasks you share with other people."
          >
            <template #icon><LucideCheckCheck class="size-5 text-ink-gray-5" /></template>
            <div class="mt-2 flex gap-2">
              <Button @click="$router.push({ name: 'Projects' })">Browse projects</Button>
              <Button v-if="permissions.canCreateTask" variant="solid" @click="showNewTask = true">
                New task
              </Button>
            </div>
          </EmptyState>

          <p v-else-if="!groups.length" class="py-10 text-center text-sm text-ink-gray-5">
            No tasks match “{{ search }}”.
          </p>

          <div v-else class="flex flex-col gap-5">
            <section v-for="group in paged.cap(groups)" :key="group.key">
              <h2 class="mb-2 flex items-center gap-2 text-sm font-semibold text-ink-gray-8">
                <span
                  v-if="group.color"
                  class="size-3 shrink-0 rounded-[4px]"
                  :style="{ backgroundColor: group.color }"
                />
                <component
                  :is="group.icon"
                  v-else-if="group.icon"
                  class="size-4"
                  :class="group.iconClass"
                />
                <span
                  v-else-if="group.dot"
                  class="size-2 shrink-0 rounded-full"
                  :class="group.dot"
                />
                {{ group.label }}
                <span class="text-xs font-normal tabular-nums text-ink-gray-5">
                  {{ group.total }}{{ group.key === 'done' && doneHasMore ? '+' : '' }}
                </span>
              </h2>

              <ul class="pb-panel overflow-hidden">
                <li
                  v-for="task in group.tasks"
                  :key="task.name"
                  class="flex cursor-pointer items-start gap-3 border-b border-outline-gray-1 bg-surface-white px-3 py-3 last:border-b-0 hover:bg-surface-gray-1 sm:items-center"
                  @click="openTask(task.name)"
                >
                  <button
                    class="mt-0.5 grid size-[18px] shrink-0 place-items-center rounded-full border transition-colors sm:mt-0"
                    :class="
                      task.status === 'Completed'
                        ? 'border-green-600 bg-green-600 text-white'
                        : 'border-outline-gray-4 hover:border-ink-gray-6'
                    "
                    :aria-label="task.status === 'Completed' ? 'Reopen task' : 'Mark complete'"
                    @click.stop="move(task, task.status === 'Completed' ? 'Open' : 'Completed')"
                  >
                    <LucideCheck v-if="task.status === 'Completed'" class="size-3" />
                  </button>

                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2">
                      <PriorityIcon :priority="task.priority" class="shrink-0" />
                      <LucideRepeat
                        v-if="task.auto_repeat"
                        class="size-3.5 shrink-0 text-ink-gray-5"
                        aria-label="Repeating task"
                      />
                      <p
                        class="min-w-0 text-sm leading-snug sm:truncate"
                        :class="
                          isDone(task) ? 'text-ink-gray-5 line-through' : 'text-ink-gray-9'
                        "
                      >
                        {{ task.subject }}
                      </p>
                      <Tooltip
                        v-if="task.my_assignment === 'done' && !isDone(task)"
                        text="You marked your part done; the task itself is still open"
                      >
                        <Badge theme="green" variant="subtle" size="sm" class="shrink-0">
                          Your part done
                        </Badge>
                      </Tooltip>
                    </div>
                    <p class="mt-0.5 flex min-w-0 items-center gap-1.5 text-xs text-ink-gray-5">
                      <span
                        v-if="task.status === 'Pending Review' && task.review_date"
                        class="inline-flex shrink-0 items-center gap-0.5"
                        :class="reviewLate(task) ? 'font-medium text-ink-red-3' : 'text-ink-amber-3'"
                      >
                        <LucideClipboardCheck class="size-3" />
                        review {{ dueLabel(task.review_date) }} ·
                      </span>
                      <span
                        v-if="task.project"
                        class="size-2 shrink-0 rounded-[3px]"
                        :style="{ backgroundColor: projectColor(task.project) }"
                      />
                      <span class="truncate">
                        {{ task.project_title || 'No project' }}
                        <template v-if="task.epic"> · {{ task.epic.subject }}</template>
                        <template v-if="task.type"> · {{ task.type }}</template>
                      </span>
                    </p>
                    <!-- on phones the meta lives under the title instead of beside it -->
                    <div class="mt-1.5 flex flex-wrap items-center gap-2 sm:hidden">
                      <div @click.stop>
                        <StatusPill
                          :status="task.status"
                          editable
                          @change="(s) => move(task, s)"
                        />
                      </div>
                      <span v-if="task.exp_end_date" class="text-xs" :class="dueClass(task)">
                        {{ dueLabel(task.exp_end_date) }}
                      </span>
                    </div>
                  </div>

                  <!-- shared work: who else is on it -->
                  <Tooltip v-if="others(task).length" :text="sharedLabel(task)">
                    <span class="hidden shrink-0 items-center gap-1 sm:flex">
                      <LucideUsers class="size-3.5 text-ink-gray-4" />
                      <AvatarStack :users="others(task)" :max="3" size="xs" />
                    </span>
                  </Tooltip>

                  <span
                    v-if="task.exp_end_date"
                    class="hidden w-16 shrink-0 text-right text-xs sm:inline"
                    :class="dueClass(task)"
                  >
                    {{ dueLabel(task.exp_end_date) }}
                  </span>
                  <div class="hidden w-28 shrink-0 sm:block" @click.stop>
                    <StatusPill :status="task.status" editable @change="(s) => move(task, s)" />
                  </div>
                </li>
              </ul>
            </section>

            <LoadMore
              v-if="hasMoreRows || (includeCompleted && doneHasMore)"
              :loading="loadingDone"
              @more="onMore"
            />
          </div>
        </section>

        <!-- side rail -->
        <aside class="flex flex-col gap-4">
          <section class="pb-panel p-4">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-sm font-semibold text-ink-gray-9">Your projects</h2>
              <router-link
                :to="{ name: 'Projects' }"
                class="text-xs text-ink-gray-5 hover:text-ink-gray-8"
              >
                All projects
              </router-link>
            </div>
            <ul class="flex flex-col gap-1">
              <li v-for="project in myProjects" :key="project.name">
                <router-link
                  :to="{ name: 'Board', params: { project: project.name } }"
                  class="-mx-2 flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-surface-gray-2"
                >
                  <span
                    class="grid size-8 shrink-0 place-items-center rounded-lg"
                    :style="{
                      backgroundColor: `${projectColor(project.name)}26`,
                      color: projectColor(project.name),
                    }"
                  >
                    <LucideFolderKanban class="size-4" />
                  </span>
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-medium text-ink-gray-8">
                      {{ project.project_name }}
                    </p>
                    <div class="mt-1 flex items-center gap-2">
                      <span class="h-1 flex-1 overflow-hidden rounded-full bg-surface-gray-2">
                        <span
                          class="block h-full rounded-full bg-surface-green-3"
                          :style="{ width: `${project.percent_complete || 0}%` }"
                        />
                      </span>
                      <span class="shrink-0 text-[11px] tabular-nums text-ink-gray-5">
                        {{ project.mine }} open for you
                      </span>
                    </div>
                  </div>
                </router-link>
              </li>
              <li v-if="!myProjects.length" class="text-xs text-ink-gray-5">
                You are not on any open project yet.
              </li>
            </ul>
            <button
              v-if="permissions.canCreateProject"
              class="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-outline-gray-3 py-2 text-sm text-ink-gray-6 transition-colors hover:border-outline-gray-4 hover:text-ink-gray-8"
              @click="showNewProject = true"
            >
              <LucidePlus class="size-4" />
              Create a project
            </button>
          </section>

          <section class="pb-panel p-4">
            <h2 class="mb-3 text-sm font-semibold text-ink-gray-9">Recently completed</h2>
            <ul class="flex flex-col gap-2.5">
              <li
                v-for="task in recentlyCompleted.slice(0, 6)"
                :key="task.name"
                class="flex cursor-pointer items-start gap-2"
                @click="openTask(task.name)"
              >
                <LucideCircleCheck class="mt-0.5 size-4 shrink-0 text-ink-green-3" />
                <div class="min-w-0">
                  <p class="truncate text-sm text-ink-gray-8 hover:underline">
                    {{ task.subject }}
                  </p>
                  <p class="truncate text-xs text-ink-gray-5">
                    {{ task.project_title || 'No project' }} ·
                    {{ timeAgo(task.completed_on || task.modified) }}
                  </p>
                </div>
              </li>
              <li v-if="!recentlyCompleted.length" class="text-xs text-ink-gray-5">
                Nothing finished in the last two weeks.
              </li>
            </ul>
          </section>

          <section class="pb-panel p-4">
            <h2 class="mb-2 text-sm font-semibold text-ink-gray-9">Quick links</h2>
            <div class="flex flex-col">
              <a
                :href="`/desk/todo?allocated_to=${encodeURIComponent(user.name || '')}`"
                target="_blank"
                rel="noopener"
                class="-mx-2 flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
              >
                <LucideListChecks class="size-4 text-ink-gray-5" />
                My ToDo list in Desk
                <LucideArrowUpRight class="ml-auto size-3.5 text-ink-gray-4" />
              </a>
              <a
                href="/desk/timesheet"
                target="_blank"
                rel="noopener"
                class="-mx-2 flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
              >
                <LucideTimer class="size-4 text-ink-gray-5" />
                Timesheets in Desk
                <LucideArrowUpRight class="ml-auto size-3.5 text-ink-gray-4" />
              </a>
              <button
                class="-mx-2 flex items-center gap-2.5 rounded-lg px-2 py-2 text-left text-sm text-ink-gray-7 hover:bg-surface-gray-2"
                @click="emitBus(EVENTS.SHOW_SHORTCUTS)"
              >
                <LucideKeyboard class="size-4 text-ink-gray-5" />
                Keyboard shortcuts
              </button>
            </div>
          </section>
        </aside>
      </div>
    </div>

    <CreateTaskDialog v-model="showNewTask" @created="load" />
    <CreateProjectDialog v-model="showNewProject" @created="onProjectCreated" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, LoadingIndicator, TabButtons, Tooltip, toast } from 'frappe-ui'
import AvatarStack from '@/components/AvatarStack.vue'
import CreateProjectDialog from '@/components/CreateProjectDialog.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadMore from '@/components/LoadMore.vue'
import PriorityIcon from '@/components/PriorityIcon.vue'
import StatTile from '@/components/StatTile.vue'
import StatusPill from '@/components/StatusPill.vue'
import api from '@/data/api'
import { usePaged } from '@/composables/usePaged'
import { emit as emitBus, EVENTS, on } from '@/data/bus'
import { batched, onListUpdate } from '@/data/realtime'
import { loadProjects, projects } from '@/data/projects'
import { boardStatuses, permissions, user } from '@/data/session'
import { projectColor, statusStyle } from '@/utils/constants'
import { dayjs, dueLabel, isOverdue, timeAgo } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

import LucideAlarmClock from '~icons/lucide/alarm-clock'
import LucideCalendarDays from '~icons/lucide/calendar-days'
import LucideCalendarRange from '~icons/lucide/calendar-range'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideCircleDashed from '~icons/lucide/circle-dashed'
import LucideCircleCheck from '~icons/lucide/circle-check'

/** How far back "recently completed" reaches. */
const RECENT_DAYS = 14

const router = useRouter()
const myTasks = ref([])
const loading = ref(false)
const includeCompleted = ref(false)
const search = ref('')
const showNewTask = ref(false)
const showNewProject = ref(false)
const reviews = ref([])

/** Older finished work, fetched 50 at a time while "Show done" is on. */
const DONE_PAGE = 50
const doneTasks = ref([])
const doneHasMore = ref(false)
const loadingDone = ref(false)
const reviewing = ref(null)

const groupBy = ref(readPref() || 'due')
function readPref() {
  try {
    return localStorage.getItem('pb:mywork-group')
  } catch {
    return null
  }
}
watch(groupBy, (value) => {
  try {
    localStorage.setItem('pb:mywork-group', value)
  } catch {
    // private mode: the choice just isn't remembered
  }
})

async function load() {
  loading.value = true
  try {
    const [rows, queue] = await Promise.all([
      api.getMyTasks(0, RECENT_DAYS),
      api.getReviewQueue(),
    ])
    myTasks.value = rows || []
    reviews.value = queue || []
    if (includeCompleted.value) await loadDone({ reset: true })
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not load your tasks')
  } finally {
    loading.value = false
  }
}

const reviewLate = (task) =>
  task.review_date && dayjs(task.review_date).isBefore(dayjs().startOf('day'))

/** Approve = Completed, send back = In Progress; either way it leaves the queue. */
async function signOff(task, status) {
  reviewing.value = task.name
  try {
    await api.moveTask(task.name, status)
    reviews.value = reviews.value.filter((t) => t.name !== task.name)
    toast.success(status === 'Completed' ? 'Approved' : 'Sent back to In Progress')
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update the task')
  } finally {
    reviewing.value = null
  }
}

async function loadDone({ reset = false } = {}) {
  if (loadingDone.value && !reset) return
  loadingDone.value = true
  try {
    const start = reset ? 0 : doneTasks.value.length
    const page = (await api.getMyDoneTasks(start, DONE_PAGE)) || []
    doneTasks.value = reset ? page : [...doneTasks.value, ...page]
    doneHasMore.value = page.length === DONE_PAGE
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not load finished tasks')
  } finally {
    loadingDone.value = false
  }
}

const isDone = (task) => ['Completed', 'Cancelled'].includes(task.status)
const others = (task) => (task.assignees || []).filter((u) => u.name !== user.value?.name)
const sharedLabel = (task) =>
  `Shared with ${others(task)
    .map((u) => u.full_name || u.name)
    .join(', ')}`
const dueClass = (task) =>
  isOverdue(task.exp_end_date, task.status) ? 'font-medium text-ink-red-3' : 'text-ink-gray-6'

const active = computed(() => myTasks.value.filter((t) => !isDone(t)))

const completedAt = (task) => dayjs(task.completed_on || task.modified)
const recentlyCompleted = computed(() => {
  const since = dayjs().subtract(RECENT_DAYS, 'day')
  return myTasks.value
    .filter((t) => t.status === 'Completed' && completedAt(t).isAfter(since))
    .sort((a, b) => completedAt(b).valueOf() - completedAt(a).valueOf())
})

/** Open work, plus every finished page fetched so far when "Show done" is on. */
const withDone = computed(() => {
  if (!includeCompleted.value) return active.value
  const seen = new Set(myTasks.value.map((t) => t.name))
  return [...myTasks.value, ...doneTasks.value.filter((t) => !seen.has(t.name))]
})

const listed = computed(() => {
  const term = search.value.trim().toLowerCase()
  return withDone.value.filter(
    (t) =>
      !term ||
      t.subject.toLowerCase().includes(term) ||
      (t.project_title || '').toLowerCase().includes(term),
  )
})

/** Due-date buckets, the way a personal queue actually reads. */
const buckets = computed(() => {
  const out = { overdue: [], today: [], week: [], later: [], someday: [] }
  const endOfToday = dayjs().endOf('day')
  const endOfWeek = dayjs().add(7, 'day').endOf('day')
  for (const task of active.value) {
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

const DUE_GROUPS = [
  { key: 'overdue', label: 'Overdue', icon: LucideAlarmClock, iconClass: 'text-ink-red-3' },
  { key: 'today', label: 'Due today', icon: LucideCalendarDays, iconClass: 'text-ink-gray-6' },
  { key: 'week', label: 'Next 7 days', icon: LucideCalendarRange, iconClass: 'text-ink-gray-6' },
  { key: 'later', label: 'Later', icon: LucideCalendarClock, iconClass: 'text-ink-gray-6' },
  { key: 'someday', label: 'No due date', icon: LucideCircleDashed, iconClass: 'text-ink-gray-5' },
]

const groups = computed(() => {
  const rows = listed.value

  if (groupBy.value === 'project') {
    const byProject = new Map()
    for (const task of rows) {
      const key = task.project || ''
      if (!byProject.has(key)) {
        byProject.set(key, {
          key: key || '__none',
          label: task.project_title || key || 'No project',
          color: key ? projectColor(key) : null,
          icon: key ? null : LucideCircleDashed,
          iconClass: 'text-ink-gray-5',
          tasks: [],
        })
      }
      byProject.get(key).tasks.push(task)
    }
    return [...byProject.values()].sort((a, b) =>
      a.key === '__none' ? 1 : b.key === '__none' ? -1 : a.label.localeCompare(b.label),
    )
  }

  if (groupBy.value === 'status') {
    const order = [...new Set([...boardStatuses.value, 'Completed', 'Cancelled'])]
    return order
      .map((status) => ({
        key: status,
        label: statusStyle(status).label || status,
        dot: statusStyle(status).dot,
        tasks: rows.filter((t) => t.status === status),
      }))
      .filter((g) => g.tasks.length)
  }

  const shown = new Set(rows.map((t) => t.name))
  const out = DUE_GROUPS.map((g) => ({
    ...g,
    tasks: buckets.value[g.key].filter((t) => shown.has(t.name)),
  }))
  if (includeCompleted.value) {
    out.push({
      key: 'done',
      label: 'Done',
      icon: LucideCircleCheck,
      iconClass: 'text-ink-green-3',
      tasks: rows.filter(isDone),
    })
  }
  return out.filter((g) => g.tasks.length)
})

// 50 rows render at a time; a new grouping or search starts from the top
const paged = usePaged(50, () => [groupBy.value, search.value, includeCompleted.value])
const hasMoreRows = computed(
  () => groups.value.reduce((n, g) => n + g.tasks.length, 0) > paged.limit.value,
)

/** Show the next rows already in hand; past those, fetch the next finished page. */
function onMore() {
  if (hasMoreRows.value) paged.more()
  else if (includeCompleted.value && doneHasMore.value) loadDone()
}

/** Projects you have open work in, then ones you are a member of, busiest first. */
const myProjects = computed(() => {
  const counts = new Map()
  for (const task of active.value) {
    if (task.project) counts.set(task.project, (counts.get(task.project) || 0) + 1)
  }
  const me = user.value?.name
  return projects.value
    .filter(
      (p) =>
        ['Open', 'On hold'].includes(p.status) &&
        (counts.has(p.name) || (p.members || []).some((m) => m.name === me)),
    )
    .map((p) => ({ ...p, mine: counts.get(p.name) || 0 }))
    .sort((a, b) => b.mine - a.mine)
    .slice(0, 6)
})

const firstName = computed(() => (user.value?.full_name || 'there').split(' ')[0])
const greeting = computed(() => {
  const hour = dayjs().hour()
  return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
})
const todayLabel = dayjs().format('dddd, D MMMM')

const summaryLine = computed(() => {
  const open = active.value.length
  if (!open) return 'Your queue is clear.'
  const parts = [`${open} open ${open === 1 ? 'task' : 'tasks'}`]
  if (buckets.value.overdue.length) parts.push(`${buckets.value.overdue.length} overdue`)
  const soon = buckets.value.today.length + buckets.value.week.length
  if (soon) parts.push(`${soon} due this week`)
  const last = parts.pop()
  return `You have ${parts.length ? `${parts.join(', ')} and ${last}` : last}.`
})

async function move(task, status) {
  const previous = task.status
  task.status = status
  try {
    const row = await api.moveTask(task.name, status)
    // the board row lacks the fields only this page adds
    Object.assign(task, row, {
      project_title: task.project_title,
      my_assignment: task.my_assignment,
    })
  } catch (e) {
    task.status = previous
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update the task')
  }
}

function onProjectCreated(name) {
  loadProjects({ force: true })
  router.push({ name: 'Board', params: { project: name } })
}

watch(includeCompleted, (on) => {
  if (on) loadDone({ reset: true })
  else doneTasks.value = []
})

// Changes made elsewhere - the board, another person, the desk - show up here
// without a refresh. A burst of edits reloads once.
const reloadSoon = batched(() => load(), 600)
let stops = []
onMounted(() => {
  stops = [on(EVENTS.TASK_UPDATED, () => reloadSoon()), onListUpdate('Task', () => reloadSoon())]
  load()
  loadProjects()
})
onUnmounted(() => stops.forEach((stop) => stop()))
</script>
