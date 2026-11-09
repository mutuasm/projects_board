<template>
  <div class="flex h-full min-h-0 flex-col">
    <!-- header -->
    <header class="shrink-0 border-b border-outline-gray-2 px-4 pt-4 sm:px-6 sm:pt-5 short:pt-2">
      <div class="flex items-center gap-2.5 sm:gap-3">
        <span
          class="grid size-9 shrink-0 place-items-center rounded-lg"
          :style="{ backgroundColor: `${color}26`, color }"
        >
          <LucideFolderKanban class="size-[18px]" />
        </span>

        <!-- the name doubles as a project switcher -->
        <Dropdown :options="switcherOptions" placement="bottom-start">
          <button
            class="-ml-1 flex min-w-0 items-center gap-1 rounded-lg px-1 py-0.5 hover:bg-surface-gray-2"
          >
            <h1
              class="min-w-0 truncate text-xl font-semibold tracking-tight text-ink-gray-9 sm:text-[26px] sm:leading-9"
            >
              {{ doc?.project_name || project }}
            </h1>
            <LucideChevronDown class="size-5 shrink-0 text-ink-gray-6" />
          </button>
        </Dropdown>

        <Badge
          v-if="doc?.status"
          :theme="projectStatusTheme"
          variant="subtle"
          size="sm"
          class="shrink-0"
        >
          {{ doc.status }}
        </Badge>
        <Badge
          v-if="doc?.priority"
          theme="gray"
          variant="subtle"
          size="sm"
          class="hidden shrink-0 lg:inline-flex"
        >
          {{ doc.priority }} priority
        </Badge>

        <div class="ml-auto flex shrink-0 items-center gap-2">
          <div v-if="doc" class="hidden items-center gap-2 xl:flex">
            <div class="text-right">
              <p class="text-xs text-ink-gray-5">Progress</p>
              <p class="text-sm font-medium text-ink-gray-8">
                {{ Math.round(doc.percent_complete || 0) }}%
              </p>
            </div>
            <div class="h-1.5 w-24 overflow-hidden rounded-full bg-surface-gray-2">
              <div
                class="h-full rounded-full bg-surface-green-3"
                :style="{ width: `${doc.percent_complete || 0}%` }"
              />
            </div>
          </div>
          <AvatarStack :users="members" :max="4" class="hidden md:flex" />
          <Tooltip text="Open this project in Desk">
            <Button class="hidden sm:inline-flex" @click="openInDesk">
              <template #prefix><LucideExternalLink class="size-4" /></template>
              Open in Desk
            </Button>
          </Tooltip>
          <Button
            v-if="permissions.canCreateTask"
            variant="solid"
            class="hidden md:inline-flex"
            @click="showNewTask = true"
          >
            <template #prefix><LucidePlus class="size-4" /></template>
            New task
          </Button>
          <Dropdown :options="projectMenu" placement="bottom-end">
            <Button variant="ghost">
              <LucideMoreHorizontal class="size-4" />
            </Button>
          </Dropdown>
        </div>
      </div>

      <!-- phones get the progress bar inline under the title -->
      <div v-if="doc" class="mt-2 flex items-center gap-2 md:hidden">
        <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-gray-2">
          <div
            class="h-full rounded-full bg-surface-green-3"
            :style="{ width: `${doc.percent_complete || 0}%` }"
          />
        </div>
        <span class="text-xs tabular-nums text-ink-gray-6">
          {{ Math.round(doc.percent_complete || 0) }}%
        </span>
        <AvatarStack :users="members" :max="3" size="xs" />
      </div>

      <!-- tabs: scroll sideways rather than wrapping on a narrow screen -->
      <nav
        class="no-scrollbar -mx-4 mt-4 flex items-center gap-5 overflow-x-auto px-4 sm:mx-0 sm:gap-7 sm:px-0 short:mt-1"
      >
        <router-link
          v-for="tab in tabs"
          :key="tab.name"
          :to="{ name: tab.name, params: { project } }"
          class="-mb-px flex shrink-0 items-center gap-2 whitespace-nowrap border-b-2 border-transparent pb-3 pt-1 text-[15px] text-ink-gray-6 transition-colors hover:text-ink-gray-9"
          active-class="!border-ink-gray-9 font-medium !text-ink-gray-9"
        >
          <component :is="tab.icon" class="size-4" />
          {{ tab.label }}
        </router-link>
      </nav>
    </header>

    <!-- paused and closed projects stay browsable; say so and offer the way back -->
    <div
      v-if="isClosed || isOnHold"
      class="flex shrink-0 items-center gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-4 py-2 text-sm text-ink-gray-7 sm:px-5"
    >
      <component
        :is="isOnHold ? LucidePauseCircle : LucideArchive"
        class="size-4 shrink-0 text-ink-gray-5"
      />
      <span class="min-w-0 flex-1">
        {{
          isOnHold
            ? 'This project is on hold.'
            : `This project was closed as ${doc.status.toLowerCase()}.`
        }}
      </span>
      <Button v-if="canEditProject" size="sm" :loading="reopening" @click="reopen">
        {{ isOnHold ? 'Resume' : 'Reopen' }}
      </Button>
    </div>

    <!-- filters -->
    <BoardFilters v-if="showFilters" class="shrink-0" />

    <!-- body -->
    <div
      class="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)] overflow-hidden"
    >
      <ErrorState v-if="error" :error="error" />
      <router-view v-else />
    </div>

    <!--
      Thumb-reachable primary action on phones. Deliberately no z-index: the
      dialogs and the task panel are portalled to the end of <body>, so leaving
      this at z-auto lets them paint over it instead of under.
    -->
    <button
      v-if="permissions.canCreateTask"
      class="fixed bottom-5 right-5 grid size-14 place-items-center rounded-full bg-surface-gray-7 text-ink-white shadow-md active:scale-95 md:hidden"
      style="margin-bottom: env(safe-area-inset-bottom)"
      aria-label="New task"
      @click="showNewTask = true"
    >
      <LucidePlus class="size-6" />
    </button>

    <CreateTaskDialog
      v-model="showNewTask"
      :project="project"
      @created="onTaskCreated"
    />

    <CloseProjectDialog
      v-model="showClose"
      :project="project"
      @closed="onClosed"
    />

    <RenameProjectDialog
      v-model="showRename"
      :project="project"
      :current-name="doc?.project_name || ''"
      @renamed="onRenamed"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Badge, Dropdown, Tooltip, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'
import api from '@/data/api'
import AvatarStack from '@/components/AvatarStack.vue'
import BoardFilters from '@/components/BoardFilters.vue'
import CloseProjectDialog from '@/components/CloseProjectDialog.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import RenameProjectDialog from '@/components/RenameProjectDialog.vue'
import ErrorState from '@/components/ErrorState.vue'
import {
  canEditProject,
  error,
  loadEpics,
  loadProject,
  members,
  projectDoc as doc,
  reloadTasks,
  upsertTask,
  watchBoardLive,
} from '@/data/board'
import { loadProjects, projects } from '@/data/projects'
import { permissions } from '@/data/session'
import { PROJECT_STATUS_STYLES, projectColor } from '@/utils/constants'

import LucideColumns3 from '~icons/lucide/columns-3'
import LucideList from '~icons/lucide/list'
import LucideGanttChart from '~icons/lucide/gantt-chart'
import LucideChartPie from '~icons/lucide/chart-pie'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucideArchive from '~icons/lucide/archive'
import LucidePauseCircle from '~icons/lucide/pause-circle'

const props = defineProps({ project: { type: String, required: true } })

const route = useRoute()
const router = useRouter()
const showNewTask = ref(false)
const showClose = ref(false)
const showRename = ref(false)
const reopening = ref(false)
const holding = ref(false)

const tabs = [
  { name: 'Board', label: 'Board', icon: LucideColumns3 },
  { name: 'TaskList', label: 'List', icon: LucideList },
  { name: 'Timeline', label: 'Timeline', icon: LucideGanttChart },
  { name: 'Overview', label: 'Overview', icon: LucideChartPie },
  { name: 'Updates', label: 'Updates', icon: LucideMegaphone },
]

const showFilters = computed(() =>
  ['Board', 'TaskList', 'Timeline'].includes(route.name),
)

const color = computed(() => projectColor(props.project))

/** Same set as the sidebar: open and paused projects, most recent first. */
const switcherOptions = computed(() => [
  {
    group: 'Switch project',
    items: projects.value
      .filter((p) => ['Open', 'On hold'].includes(p.status) && p.name !== props.project)
      .slice(0, 12)
      .map((p) => ({
        label: p.project_name,
        onClick: () => router.push({ name: route.name, params: { project: p.name } }),
      })),
  },
  {
    group: '',
    items: [
      { label: 'All projects', icon: 'grid', onClick: () => router.push({ name: 'Projects' }) },
    ],
  },
])

// a new tab, so the board stays where it was
function openInDesk() {
  window.open(`/desk/project/${props.project}`, '_blank')
}

const projectStatusTheme = computed(
  () => PROJECT_STATUS_STYLES[doc.value?.status]?.theme || 'gray',
)

const isClosed = computed(() => ['Completed', 'Cancelled'].includes(doc.value?.status))
const isOnHold = computed(() => doc.value?.status === 'On hold')

const projectMenu = computed(() => [
  {
    label: 'Refresh',
    icon: 'refresh-cw',
    onClick: () => loadProject(props.project, { force: true }),
  },
  ...(canEditProject.value && doc.value
    ? [
        { label: 'Rename project', icon: 'pencil', onClick: () => (showRename.value = true) },
        ...statusActions.value,
      ]
    : []),
])

const statusActions = computed(() => {
  if (isClosed.value) return [{ label: 'Reopen project', icon: 'rotate-ccw', onClick: reopen }]
  return [
    isOnHold.value
      ? { label: 'Resume project', icon: 'play-circle', onClick: reopen }
      : { label: 'Put on hold', icon: 'pause-circle', onClick: putOnHold },
    { label: 'Close project', icon: 'archive', onClick: () => (showClose.value = true) },
  ]
})

async function onClosed({ doc: updated, cancelOpenTasks }) {
  doc.value = updated
  toast.success(`Project closed as ${updated.status.toLowerCase()}`)
  // the sidebar only lists open projects
  loadProjects({ force: true })
  if (cancelOpenTasks) await Promise.all([reloadTasks(), loadEpics(props.project)])
}

function onRenamed(updated) {
  doc.value = updated
  toast.success('Project renamed')
  // the sidebar, switcher and palette list projects by name
  loadProjects({ force: true })
}

// ERPNext leaves On hold alone when it recomputes a project's status from its
// tasks, so pausing is a plain status write.
async function putOnHold() {
  if (holding.value) return
  holding.value = true
  try {
    doc.value = await api.updateProject(props.project, { status: 'On hold' })
    loadProjects({ force: true })
    toast.success('Project put on hold')
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not put the project on hold')
  } finally {
    holding.value = false
  }
}

async function reopen() {
  const resuming = isOnHold.value
  reopening.value = true
  try {
    const updated = await api.updateProject(props.project, { status: 'Open' })
    doc.value = updated
    loadProjects({ force: true })
    // ERPNext's task-based % complete puts a project with every task done
    // straight back to Completed, so the reopen does not stick.
    if (updated.status === 'Open') toast.success(resuming ? 'Project resumed' : 'Project reopened')
    else toast.error('Every task is done, so ERPNext marks it Completed. Reopen or add a task first.')
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not reopen the project')
  } finally {
    reopening.value = false
  }
}

function onTaskCreated(task) {
  upsertTask(task)
}

watch(
  () => props.project,
  (name) => name && loadProject(name),
  { immediate: true },
)

let stopLive = null
onMounted(() => (stopLive = watchBoardLive()))
onUnmounted(() => stopLive?.())
</script>
