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
          :buttons="[
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
        <div class="relative min-w-0 flex-1 sm:max-w-xs">
          <LucideSearch
            class="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-ink-gray-4"
          />
          <input
            v-model="search"
            type="text"
            placeholder="Search projects"
            class="pb-input h-9 w-full pl-7 pr-2 text-base sm:h-7 sm:text-sm"
          />
        </div>
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
          class="pb-card flex flex-col gap-3 !rounded-xl p-4"
        >
          <div class="flex items-start gap-3">
            <span
              class="grid size-9 shrink-0 place-items-center rounded-lg"
              :style="{
                backgroundColor: `${projectColor(project.name)}26`,
                color: projectColor(project.name),
              }"
            >
              <LucideFolderKanban class="size-[18px]" />
            </span>
            <div class="min-w-0 flex-1">
              <h2 class="truncate text-base font-medium text-ink-gray-9">
                {{ project.project_name }}
              </h2>
              <p class="truncate text-xs text-ink-gray-5">
                {{ project.project_type || 'No type' }}
                <span v-if="project.customer"> · {{ project.customer }}</span>
              </p>
            </div>
            <Badge
              :theme="PROJECT_STATUS_STYLES[project.status]?.theme || 'gray'"
              variant="subtle"
              size="sm"
            >
              {{ project.status }}
            </Badge>
          </div>

          <div>
            <div class="mb-1 flex items-baseline justify-between text-xs">
              <span class="text-ink-gray-5">
                {{ project.open_tasks }} open / {{ project.total_tasks }} tasks
              </span>
              <span class="font-medium tabular-nums text-ink-gray-7">
                {{ Math.round(project.percent_complete || 0) }}%
              </span>
            </div>
            <div class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2">
              <div
                class="h-full rounded-full bg-surface-green-3"
                :style="{ width: `${project.percent_complete || 0}%` }"
              />
            </div>
          </div>

          <div class="flex items-center gap-2">
            <AvatarStack :users="project.members" :max="4" size="xs" />
            <span
              v-if="project.expected_end_date"
              class="ml-auto inline-flex items-center gap-1 text-xs"
              :class="
                isOverdue(project.expected_end_date, project.status)
                  ? 'font-medium text-ink-red-3'
                  : 'text-ink-gray-5'
              "
            >
              <LucideCalendar class="size-3" />
              {{ formatDate(project.expected_end_date) }}
            </span>
          </div>
        </router-link>
      </div>

      <!-- table -->
      <div
        v-else
        class="pb-panel thin-scrollbar overflow-x-auto"
      >
        <table class="w-full min-w-[46rem] text-sm">
          <thead class="bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
            <tr>
              <th class="px-3 py-2 text-left font-medium">Project</th>
              <th class="px-3 py-2 text-left font-medium">Status</th>
              <th class="px-3 py-2 text-left font-medium">Open</th>
              <th class="px-3 py-2 text-left font-medium">Progress</th>
              <th class="px-3 py-2 text-left font-medium">Due</th>
              <th class="px-3 py-2 text-left font-medium">Team</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="project in paged.slice(filtered)"
              :key="project.name"
              class="cursor-pointer border-t border-outline-gray-1 bg-surface-white hover:bg-surface-gray-1"
              @click="$router.push({ name: 'Board', params: { project: project.name } })"
            >
              <td class="px-3 py-2">
                <div class="flex items-center gap-2.5">
                  <span
                    class="size-3 shrink-0 rounded-[4px]"
                    :style="{ backgroundColor: projectColor(project.name) }"
                  />
                  <div class="min-w-0">
                    <p class="font-medium text-ink-gray-8">{{ project.project_name }}</p>
                    <p class="text-xs text-ink-gray-5">{{ project.name }}</p>
                  </div>
                </div>
              </td>
              <td class="px-3 py-2">
                <Badge
                  :theme="PROJECT_STATUS_STYLES[project.status]?.theme || 'gray'"
                  variant="subtle"
                  size="sm"
                >
                  {{ project.status }}
                </Badge>
              </td>
              <td class="px-3 py-2 tabular-nums text-ink-gray-7">
                {{ project.open_tasks }}/{{ project.total_tasks }}
              </td>
              <td class="px-3 py-2">
                <div class="flex items-center gap-2">
                  <div class="h-1.5 w-20 overflow-hidden rounded-full bg-surface-gray-2">
                    <div
                      class="h-full rounded-full bg-surface-green-3"
                      :style="{ width: `${project.percent_complete || 0}%` }"
                    />
                  </div>
                  <span class="text-xs tabular-nums text-ink-gray-6">
                    {{ Math.round(project.percent_complete || 0) }}%
                  </span>
                </div>
              </td>
              <td
                class="px-3 py-2 text-xs"
                :class="
                  isOverdue(project.expected_end_date, project.status)
                    ? 'font-medium text-ink-red-3'
                    : 'text-ink-gray-6'
                "
              >
                {{ formatDate(project.expected_end_date) || '—' }}
              </td>
              <td class="px-3 py-2">
                <AvatarStack :users="project.members" :max="3" size="xs" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <LoadMore v-if="filtered.length > paged.limit.value" @more="paged.more" />
    </div>

    <CreateProjectDialog v-model="showNew" @created="onCreated" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, LoadingIndicator, TabButtons } from 'frappe-ui'
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
