<template>
  <div class="flex h-full min-h-0 flex-col">
    <!-- header -->
    <header class="shrink-0 border-b border-outline-gray-2 px-5 pt-4">
      <div class="flex items-start gap-3">
        <div class="min-w-0 flex-1">
          <Breadcrumbs :items="breadcrumbs" />
          <div class="mt-1 flex flex-wrap items-center gap-2">
            <h1 class="truncate text-xl font-semibold text-ink-gray-9">
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
            <Badge v-if="doc?.priority" theme="gray" variant="subtle" size="sm">
              {{ doc.priority }} priority
            </Badge>
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
          <AvatarStack :users="members" :max="4" />
          <Button
            v-if="permissions.canCreateTask"
            variant="solid"
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

      <!-- tabs -->
      <nav class="mt-3 flex items-center gap-1">
        <router-link
          v-for="tab in tabs"
          :key="tab.name"
          :to="{ name: tab.name, params: { project } }"
          class="flex items-center gap-1.5 border-b-2 border-transparent px-2.5 pb-2 pt-1 text-sm text-ink-gray-6 hover:text-ink-gray-9"
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
      <div v-if="loading" class="flex h-full items-center justify-center">
        <LoadingIndicator class="size-6 text-ink-gray-5" />
      </div>
      <ErrorState v-else-if="error" :error="error" />
      <router-view v-else />
    </div>

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
import { Badge, Breadcrumbs, Dropdown, LoadingIndicator } from 'frappe-ui'
import AvatarStack from '@/components/AvatarStack.vue'
import BoardFilters from '@/components/BoardFilters.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import ErrorState from '@/components/ErrorState.vue'
import {
  error,
  loadProject,
  loading,
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

const props = defineProps({ project: { type: String, required: true } })

const route = useRoute()
const showNewTask = ref(false)

const tabs = [
  { name: 'Board', label: 'Board', icon: LucideColumns3 },
  { name: 'TaskList', label: 'List', icon: LucideList },
  { name: 'Timeline', label: 'Timeline', icon: LucideGanttChart },
  { name: 'Overview', label: 'Overview', icon: LucideChartPie },
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
