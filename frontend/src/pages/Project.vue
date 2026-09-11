<template>
  <div class="flex h-full min-h-0 flex-col">
    <!-- header -->
    <header
      class="shrink-0 border-b border-outline-gray-2 px-4 pt-safe-top sm:px-5 sm:pt-4 short:sm:pt-2"
    >
      <div class="flex items-start gap-2 pt-3 sm:gap-3 sm:pt-0">
        <SidebarToggle class="mt-0.5" />
        <div class="min-w-0 flex-1">
          <Breadcrumbs :items="breadcrumbs" class="hidden sm:block short:!hidden" />
          <div class="mt-0 flex flex-wrap items-center gap-2 sm:mt-1">
            <h1
              class="min-w-0 truncate text-lg font-semibold text-ink-gray-9 sm:text-xl"
            >
              {{ doc?.project_name || project }}
            </h1>
            <Badge
              v-if="doc?.status"
              :theme="projectStatusTheme"
              variant="subtle"
              size="sm"
            >
              {{ doc.status }}
            </Badge>
            <Badge
              v-if="doc?.priority"
              theme="gray"
              variant="subtle"
              size="sm"
              class="hidden sm:inline-flex"
            >
              {{ doc.priority }} priority
            </Badge>
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
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <div v-if="doc" class="hidden items-center gap-2 md:flex">
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

      <!-- tabs: scroll sideways rather than wrapping on a narrow screen -->
      <nav
        class="no-scrollbar -mx-4 mt-3 flex items-center gap-1 overflow-x-auto px-4 sm:mx-0 sm:px-0 short:mt-1"
      >
        <router-link
          v-for="tab in tabs"
          :key="tab.name"
          :to="{ name: tab.name, params: { project } }"
          class="flex shrink-0 items-center gap-1.5 whitespace-nowrap border-b-2 border-transparent px-2.5 pb-2 pt-1 text-sm text-ink-gray-6 hover:text-ink-gray-9"
          active-class="!border-outline-gray-5 font-medium !text-ink-gray-9"
        >
          <component :is="tab.icon" class="size-4" />
          {{ tab.label }}
        </router-link>
      </nav>
    </header>

    <!-- filters -->
    <BoardFilters v-if="showFilters" class="shrink-0" />

    <!-- body -->
    <div class="min-h-0 flex-1 overflow-hidden">
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
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Badge, Breadcrumbs, Dropdown } from 'frappe-ui'
import AvatarStack from '@/components/AvatarStack.vue'
import BoardFilters from '@/components/BoardFilters.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import ErrorState from '@/components/ErrorState.vue'
import SidebarToggle from '@/components/SidebarToggle.vue'
import {
  error,
  loadProject,
  members,
  projectDoc as doc,
  upsertTask,
} from '@/data/board'
import { permissions } from '@/data/session'
import { PROJECT_STATUS_STYLES } from '@/utils/constants'

import LucideColumns3 from '~icons/lucide/columns-3'
import LucideList from '~icons/lucide/list'
import LucideGanttChart from '~icons/lucide/gantt-chart'
import LucideChartPie from '~icons/lucide/chart-pie'
import LucideMegaphone from '~icons/lucide/megaphone'

const props = defineProps({ project: { type: String, required: true } })

const route = useRoute()
const showNewTask = ref(false)

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

const breadcrumbs = computed(() => [
  { label: 'Projects', route: { name: 'Projects' } },
  { label: doc.value?.project_name || props.project },
])

const projectStatusTheme = computed(
  () => PROJECT_STATUS_STYLES[doc.value?.status]?.theme || 'gray',
)

const projectMenu = computed(() => [
  {
    label: 'Open in Desk',
    icon: 'external-link',
    onClick: () => window.open(`/app/project/${props.project}`, '_blank'),
  },
  {
    label: 'Refresh',
    icon: 'refresh-cw',
    onClick: () => loadProject(props.project, { force: true }),
  },
])

function onTaskCreated(task) {
  upsertTask(task)
}

watch(
  () => props.project,
  (name) => name && loadProject(name),
  { immediate: true },
)
</script>
