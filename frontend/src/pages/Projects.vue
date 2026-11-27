<template>
  <div class="flex h-full min-h-0 flex-col">
    <PageHeader>
      <template #title>
        <h1 class="truncate font-medium">Projects</h1>
        <span class="shrink-0 text-base text-ink-gray-5">
          {{ filtered.length }} of {{ projects.length }}
        </span>
      </template>
      <template #actions>
        <TabButtons
          v-if="!isNarrow"
          v-model="layout"
          :options="[
            { label: 'Cards', value: 'cards' },
            { label: 'Table', value: 'table' },
          ]"
        />
        <Button
          v-if="permissions.canCreateProject"
          variant="solid"
          @click="showNew = true"
        >
          <template #prefix><LucidePlus class="size-4" /></template>
          <span class="hidden sm:inline">New project</span>
        </Button>
      </template>
    </PageHeader>

    <header class="shrink-0 border-b border-outline-gray-2 px-4 py-2.5 sm:px-5">
      <!-- search + status sit on their own row so neither gets squeezed -->
      <div class="flex items-center gap-2">
        <TextInput
          v-model="search"
          type="search"
          placeholder="Search projects"
          class="min-w-0 flex-1 sm:max-w-xs"
        >
          <template #prefix><LucideSearch class="size-3.5 text-ink-gray-5" /></template>
        </TextInput>
        <!-- Select hardcodes w-full on its trigger, so size it from a wrapper -->
        <div class="w-32 shrink-0">
          <NullableSelect v-model="statusFilter" :options="statusOptions" />
        </div>
      </div>
    </header>

    <div class="thin-scrollbar min-h-0 flex-1 overflow-y-auto px-4 py-4 pb-safe-bottom sm:px-5">
      <div v-if="loadingProjects && !projects.length" class="flex h-40 items-center justify-center">
        <LoadingIndicator class="size-5 text-ink-gray-5" />
      </div>

      <EmptyState
        v-else-if="!filtered.length"
        :title="projects.length ? 'No projects match' : 'No projects yet'"
        :description="
          projects.length
            ? 'Try a different search or status filter.'
            : 'Create your first project to start planning work.'
        "
      >
        <template #icon><LucideLayoutGrid class="size-5 text-ink-gray-5" /></template>
        <Button
          v-if="permissions.canCreateProject && !projects.length"
          class="mt-2"
          variant="solid"
          @click="showNew = true"
        >
          New project
        </Button>
      </EmptyState>

      <!-- cards -->
      <div
        v-else-if="effectiveLayout === 'cards'"
        class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
      >
        <router-link
          v-for="project in paged.slice(filtered)"
          :key="project.name"
          :to="{ name: 'Board', params: { project: project.name } }"
          class="pb-card flex flex-col gap-3 p-4"
        >
          <div class="flex items-start gap-2.5">
            <span
              class="mt-1.5 size-2.5 shrink-0 rounded-[3px]"
              :style="{ backgroundColor: projectColor(project.name) }"
            />
            <div class="min-w-0 flex-1">
              <h2 class="truncate text-base-medium text-ink-gray-9">
                {{ project.project_name }}
              </h2>
              <p
                v-if="project.project_type || project.customer"
                class="truncate text-sm text-ink-gray-5"
              >
                {{ [project.project_type, project.customer].filter(Boolean).join(' · ') }}
              </p>
            </div>
            <!-- Open is the normal state; only say something when it isn't -->
            <Badge
              v-if="project.status !== 'Open'"
              :theme="PROJECT_STATUS_STYLES[project.status]?.theme || 'gray'"
              variant="subtle"
              size="sm"
            >
              {{ project.status }}
            </Badge>
          </div>

          <div class="mt-auto">
            <div class="mb-1.5 flex items-center gap-2 text-sm text-ink-gray-5">
              <span>
                {{
                  project.total_tasks
                    ? `${project.open_tasks} open of ${project.total_tasks}`
                    : 'No tasks yet'
                }}
              </span>
              <span
                v-if="project.expected_end_date"
                :class="
                  isOverdue(project.expected_end_date, project.status) ? 'text-ink-red-5' : ''
                "
              >
                · due {{ formatDate(project.expected_end_date) }}
              </span>
              <AvatarStack
                v-if="project.members?.length"
                :users="project.members"
                :max="3"
                size="xs"
                class="ml-auto"
              />
            </div>
            <div class="flex items-center gap-2">
              <div class="h-1 flex-1 overflow-hidden rounded-full bg-surface-gray-2">
                <div
                  class="h-full rounded-full bg-surface-green-7"
                  :style="{ width: `${project.percent_complete || 0}%` }"
                />
              </div>
              <span class="w-8 text-right text-xs tabular-nums text-ink-gray-5">
                {{ Math.round(project.percent_complete || 0) }}%
              </span>
            </div>
          </div>
        </router-link>
      </div>

      <!-- table: frappe-ui's ListView, the same list CRM and Helpdesk use -->
      <ListView
        v-else
        class="h-auto"
        :columns="tableColumns"
        :rows="paged.slice(filtered)"
        row-key="name"
        :options="{
          selectable: false,
          showTooltip: false,
          getRowRoute: (row) => ({ name: 'Board', params: { project: row.name } }),
        }"
      >
        <template #cell="{ column, row }">
          <div v-if="column.key === 'project_name'" class="flex min-w-0 items-center gap-2.5">
            <span
              class="size-2.5 shrink-0 rounded-[3px]"
              :style="{ backgroundColor: projectColor(row.name) }"
            />
            <span class="truncate text-base text-ink-gray-9">{{ row.project_name }}</span>
          </div>
          <Badge
            v-else-if="column.key === 'status'"
            :theme="PROJECT_STATUS_STYLES[row.status]?.theme || 'gray'"
            variant="subtle"
          >
            {{ row.status }}
          </Badge>
          <span v-else-if="column.key === 'open_tasks'" class="tabular-nums text-ink-gray-7">
            {{ row.open_tasks }} of {{ row.total_tasks }}
          </span>
          <div v-else-if="column.key === 'percent_complete'" class="flex w-full items-center gap-2">
            <div class="h-1 flex-1 overflow-hidden rounded-full bg-surface-gray-2">
              <div
                class="h-full rounded-full bg-surface-green-7"
                :style="{ width: `${row.percent_complete || 0}%` }"
              />
            </div>
            <span class="w-8 text-right text-sm tabular-nums text-ink-gray-5">
              {{ Math.round(row.percent_complete || 0) }}%
            </span>
          </div>
          <span
            v-else-if="column.key === 'expected_end_date'"
            :class="
              isOverdue(row.expected_end_date, row.status) ? 'text-ink-red-5' : 'text-ink-gray-6'
            "
          >
            {{ formatDate(row.expected_end_date) || '—' }}
          </span>
          <AvatarStack
            v-else-if="column.key === 'members' && row.members?.length"
            :users="row.members"
            :max="3"
            size="xs"
          />
        </template>
      </ListView>

      <LoadMore v-if="filtered.length > paged.limit.value" @more="paged.more" />
    </div>

    <CreateProjectDialog v-model="showNew" @created="onCreated" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, LoadingIndicator, TabButtons, TextInput } from 'frappe-ui'
// ListView stays in experimental until frappe-ui/list reaches parity
import { ListView } from 'frappe-ui/experimental'
import NullableSelect from '@/components/NullableSelect.vue'
import PageHeader from '@/components/PageHeader.vue'
import AvatarStack from '@/components/AvatarStack.vue'
import CreateProjectDialog from '@/components/CreateProjectDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import { loadProjects, loadingProjects, projects } from '@/data/projects'
import { isNarrow } from '@/data/ui'
import { permissions, projectStatuses } from '@/data/session'
import { PROJECT_STATUS_STYLES, projectColor } from '@/utils/constants'
import { formatDate, isOverdue } from '@/utils/format'
import LoadMore from '@/components/LoadMore.vue'
import { usePaged } from '@/composables/usePaged'

const router = useRouter()
const search = ref('')
// Paused projects are still live work, so the default view keeps them.
const ACTIVE = 'active'
const statusFilter = ref(ACTIVE)
const layout = ref(localStorage.getItem('pb:projects-layout') || 'cards')
const showNew = ref(false)

/** A six-column table is unreadable on a phone, so force cards there. */
const effectiveLayout = computed(() => (isNarrow.value ? 'cards' : layout.value))

const statusOptions = computed(() => [
  { label: 'All statuses', value: '' },
  { label: 'Active', value: ACTIVE },
  ...projectStatuses.value.map((s) => ({ label: s, value: s })),
])

const tableColumns = [
  { label: 'Project', key: 'project_name', width: 3 },
  { label: 'Status', key: 'status', width: '8rem' },
  { label: 'Open tasks', key: 'open_tasks', width: '8rem' },
  { label: 'Progress', key: 'percent_complete', width: '11rem' },
  { label: 'Due', key: 'expected_end_date', width: '8rem' },
  { label: 'Team', key: 'members', width: '7rem' },
]

const filtered = computed(() => {
  const term = search.value.trim().toLowerCase()
  return projects.value.filter((project) => {
    if (statusFilter.value === ACTIVE) {
      if (!['Open', 'On hold'].includes(project.status)) return false
    } else if (statusFilter.value && project.status !== statusFilter.value) {
      return false
    }
    if (term && !project.project_name.toLowerCase().includes(term)) return false
    return true
  })
})

// 40 at a time; a new search, filter or layout starts from the top
const paged = usePaged(40, () => [search.value, statusFilter.value, layout.value])

watch(layout, (value) => localStorage.setItem('pb:projects-layout', value))

function onCreated(name) {
  loadProjects({ force: true })
  router.push({ name: 'Board', params: { project: name } })
}

onMounted(() => loadProjects())
</script>
