<template>
  <div class="flex h-full min-h-0 flex-col">
    <PageHeader>
      <template #title>
        <h1 class="truncate font-medium">My Work</h1>
        <span v-if="active.length" class="shrink-0 text-base text-ink-gray-5">
          {{ active.length }} open
        </span>
      </template>
      <template #actions>
        <Dropdown :options="moreMenu" placement="right">
          <Button variant="ghost" label="More">
            <LucideMoreHorizontal class="size-4" />
          </Button>
        </Dropdown>
        <Button v-if="permissions.canCreateTask" variant="solid" @click="showNewTask = true">
          <template #prefix><LucidePlus class="size-4" /></template>
          <span class="hidden sm:inline">New task</span>
        </Button>
      </template>
    </PageHeader>

    <!-- list controls sit in one strip under the header, like a CRM list view -->
    <div
      class="flex shrink-0 flex-wrap items-center gap-2 border-b border-outline-gray-2 px-4 py-2.5 sm:px-5"
    >
      <div class="relative min-w-0 basis-full sm:max-w-xs sm:flex-1 sm:basis-auto">
        <LucideSearch
          class="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-ink-gray-4"
        />
        <input
          v-model="search"
          type="search"
          placeholder="Filter my tasks"
          class="pb-input h-9 w-full pl-7 pr-2 text-base sm:h-7 sm:text-sm"
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
        <Button variant="ghost" :loading="loading" label="Refresh" @click="load">
          <LucideRefreshCw class="size-4" />
        </Button>
      </Tooltip>
    </div>

    <div class="thin-scrollbar min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-5xl px-4 pb-safe-bottom pt-6 sm:px-6">
        <!-- the one line that matters most, then the quiet context -->
        <div v-if="active.length" class="mb-6">
          <p class="text-xl font-semibold text-ink-gray-9">{{ headline }}</p>
          <p class="mt-1 text-sm text-ink-gray-5">{{ todayLabel }} · {{ contextLine }}</p>
        </div>

        <!-- sign-offs come first: they block someone else -->
        <section v-if="reviews.length" class="mb-8">
          <h2 class="mb-2 flex items-center gap-2 text-sm font-medium text-ink-gray-9">
            <LucideClipboardCheck class="size-4 text-ink-amber-3" />
            Waiting on your review
            <span class="tabular-nums text-ink-gray-5">{{ reviews.length }}</span>
          </h2>
          <ul class="pb-panel overflow-hidden">
            <li
              v-for="task in reviews"
              :key="task.name"
              class="flex cursor-pointer flex-wrap items-center gap-3 border-b border-outline-gray-1 px-3 py-2.5 last:border-b-0 hover:bg-surface-gray-1"
              @click="openTask(task.name)"
            >
              <AvatarStack :users="task.assignees || []" :max="2" size="sm" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-base text-ink-gray-9">{{ task.subject }}</p>
                <p class="flex items-center gap-1.5 truncate text-sm text-ink-gray-5">
                  {{ task.project_title || 'No project' }}
                  <template v-if="task.review_date">
                    ·
                    <span :class="reviewLate(task) ? 'text-ink-red-3' : ''">
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

        <div v-else class="flex flex-col gap-6 pb-8">
          <section v-for="group in paged.cap(groups)" :key="group.key">
            <!-- group head: collapsible, so a long "No due date" can be tucked away -->
            <button
              class="flex w-full items-center gap-2 border-b border-outline-gray-2 pb-2 text-left text-sm font-medium"
              :class="group.key === 'overdue' ? 'text-ink-red-4' : 'text-ink-gray-9'"
              :aria-expanded="!collapsed.has(group.key)"
              @click="toggleGroup(group.key)"
            >
              <LucideChevronRight
                class="size-3.5 shrink-0 text-ink-gray-5 transition-transform"
                :class="!collapsed.has(group.key) && 'rotate-90'"
              />
              <span
                v-if="group.color"
                class="size-2.5 shrink-0 rounded-[3px]"
                :style="{ backgroundColor: group.color }"
              />
              <span
                v-else-if="group.dot"
                class="size-2 shrink-0 rounded-full"
                :class="group.dot"
              />
              {{ group.label }}
              <span class="font-normal tabular-nums text-ink-gray-5">
                {{ group.total }}{{ group.key === 'done' && doneHasMore ? '+' : '' }}
              </span>
            </button>

            <ul v-show="!collapsed.has(group.key)">
              <li
                v-for="task in group.tasks"
                :key="task.name"
                class="group flex cursor-pointer items-start gap-3 border-b border-outline-gray-1 px-1 py-2.5 hover:bg-surface-gray-1 sm:items-center"
                @click="openTask(task.name)"
              >
                <button
                  class="mt-0.5 grid size-4 shrink-0 place-items-center rounded-full border transition-colors sm:mt-0"
                  :class="
                    task.status === 'Completed'
                      ? 'border-green-600 bg-green-600 text-white'
                      : 'border-outline-gray-4 hover:border-ink-gray-6'
                  "
                  :aria-label="task.status === 'Completed' ? 'Reopen task' : 'Mark complete'"
                  @click.stop="move(task, task.status === 'Completed' ? 'Open' : 'Completed')"
                >
                  <LucideCheck v-if="task.status === 'Completed'" class="size-2.5" />
                </button>

                <!-- the title carries the row; everything else is context -->
                <div class="min-w-0 flex-1">
                  <div class="flex min-w-0 items-center gap-2">
                    <PriorityIcon
                      v-if="isNotablePriority(task.priority)"
                      :priority="task.priority"
                      class="shrink-0"
                    />
                    <LucideRepeat
                      v-if="task.auto_repeat"
                      class="size-3.5 shrink-0 text-ink-gray-4"
                      aria-label="Repeating task"
                    />
                    <p
                      class="min-w-0 text-base leading-snug sm:truncate"
                      :class="isDone(task) ? 'text-ink-gray-5 line-through' : 'text-ink-gray-9'"
                    >
                      {{ task.subject }}
                    </p>
                    <Tooltip
                      v-if="task.my_assignment === 'done' && !isDone(task)"
                      text="You marked your part done; the task itself is still open"
                    >
                      <LucideCircleCheck class="size-3.5 shrink-0 text-ink-green-3" />
                    </Tooltip>
                  </div>
                  <!-- phones: one muted line under the title -->
                  <p class="mt-0.5 flex min-w-0 items-center gap-1.5 text-sm text-ink-gray-5 md:hidden">
                    <span class="truncate">{{ task.project_title || 'No project' }}</span>
                    <template v-if="task.exp_end_date">
                      · <span class="shrink-0" :class="dueClass(task)">{{ dueLabel(task.exp_end_date) }}</span>
                    </template>
                  </p>
                </div>

                <span
                  v-if="task.status === 'Pending Review' && task.review_date"
                  class="hidden shrink-0 items-center gap-1 text-sm md:inline-flex"
                  :class="reviewLate(task) ? 'text-ink-red-3' : 'text-ink-amber-3'"
                >
                  <LucideClipboardCheck class="size-3.5" />
                  {{ dueLabel(task.review_date) }}
                </span>

                <Tooltip v-if="others(task).length" :text="sharedLabel(task)">
                  <span class="hidden shrink-0 md:flex">
                    <AvatarStack :users="others(task)" :max="3" size="xs" />
                  </span>
                </Tooltip>

                <span
                  class="hidden w-56 shrink-0 items-center gap-1.5 text-sm text-ink-gray-5 md:flex"
                  :title="contextOf(task)"
                >
                  <span
                    v-if="task.project"
                    class="size-2 shrink-0 rounded-[3px]"
                    :style="{ backgroundColor: projectColor(task.project) }"
                  />
                  <span class="truncate">
                    {{ task.project_title || 'No project' }}
                    <span v-if="task.epic" class="text-ink-gray-4"> · {{ task.epic.subject }}</span>
                  </span>
                </span>

                <span class="hidden w-20 shrink-0 text-right text-sm md:inline" :class="dueClass(task)">
                  {{ task.exp_end_date ? dueLabel(task.exp_end_date) : '' }}
                </span>
                <div class="shrink-0 md:w-28" @click.stop>
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
      </div>
    </div>

    <CreateTaskDialog v-model="showNewTask" @created="load" />
    <CreateProjectDialog v-model="showNewProject" @created="onProjectCreated" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dropdown, LoadingIndicator, TabButtons, Tooltip, toast } from 'frappe-ui'
import AvatarStack from '@/components/AvatarStack.vue'
import PageHeader from '@/components/PageHeader.vue'
import CreateProjectDialog from '@/components/CreateProjectDialog.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadMore from '@/components/LoadMore.vue'
import PriorityIcon from '@/components/PriorityIcon.vue'
import StatusPill from '@/components/StatusPill.vue'
import api from '@/data/api'
import { usePaged } from '@/composables/usePaged'
import { EVENTS, on } from '@/data/bus'
import { batched, onListUpdate } from '@/data/realtime'
import { loadProjects } from '@/data/projects'
import { boardStatuses, permissions, user } from '@/data/session'
import { isNotablePriority, projectColor, statusStyle } from '@/utils/constants'
import { dayjs, dueLabel, isOverdue } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'


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

/** Groups folded away, remembered per browser. */
const collapsed = ref(new Set(readCollapsed()))
function readCollapsed() {
  try {
    return JSON.parse(localStorage.getItem('pb:mywork-collapsed') || '[]')
  } catch {
    return []
  }
}
function toggleGroup(key) {
  const next = new Set(collapsed.value)
  next.has(key) ? next.delete(key) : next.add(key)
  collapsed.value = next
  try {
    localStorage.setItem('pb:mywork-collapsed', JSON.stringify([...next]))
  } catch {
    // private mode
  }
}

/** Things you reach for now and then, kept out of the way. */
const moreMenu = computed(() => [
  ...(permissions.value.canCreateProject
    ? [{ label: 'New project', icon: 'folder-plus', onClick: () => (showNewProject.value = true) }]
    : []),
  {
    label: 'My ToDo list in Desk',
    icon: 'external-link',
    onClick: () =>
      window.open(`/desk/todo?allocated_to=${encodeURIComponent(user.value?.name || '')}`, '_blank'),
  },
  {
    label: 'Timesheets in Desk',
    icon: 'external-link',
    onClick: () => window.open('/desk/timesheet', '_blank'),
  },
])

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
  { key: 'overdue', label: 'Overdue' },
  { key: 'today', label: 'Due today' },
  { key: 'week', label: 'Next 7 days' },
  { key: 'later', label: 'Later' },
  { key: 'someday', label: 'No due date' },
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

const todayLabel = dayjs().format('dddd, D MMMM')

/** What needs you first, in a few words. */
const headline = computed(() => {
  const late = buckets.value.overdue.length
  const today = buckets.value.today.length
  const week = buckets.value.week.length
  const parts = []
  if (late) parts.push(`${late} overdue`)
  if (today) parts.push(`${today} due today`)
  if (week) parts.push(`${week} due this week`)
  return parts.length ? parts.join(', ') : 'Nothing due this week'
})

const contextLine = computed(() => {
  const open = active.value.length
  const done = recentlyCompleted.value.length
  return `${open} open ${open === 1 ? 'task' : 'tasks'} · ${done} done in the last ${RECENT_DAYS} days`
})

const contextOf = (task) =>
  [task.project_title || 'No project', task.epic?.subject].filter(Boolean).join(' · ')

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
