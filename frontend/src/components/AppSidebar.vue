<template>
  <aside
    class="flex h-full shrink-0 flex-col border-r border-outline-gray-2 bg-surface-menu-bar transition-all duration-200"
    :class="collapsed ? 'w-14' : 'w-60'"
  >
    <!-- brand -->
    <div class="flex items-center gap-2 px-3 py-3">
      <div
        class="grid size-7 shrink-0 place-items-center rounded bg-surface-gray-7 text-ink-white"
      >
        <LucideKanban class="size-4" />
      </div>
      <span v-if="!collapsed" class="truncate text-base font-semibold text-ink-gray-8">
        Project Board
      </span>
      <button
        class="ml-auto rounded p-1 text-ink-gray-5 hover:bg-surface-gray-2"
        :title="collapsed ? 'Expand' : 'Collapse'"
        @click="toggle"
      >
        <LucidePanelLeft class="size-4" />
      </button>
    </div>

    <!-- primary nav -->
    <nav class="flex flex-col gap-0.5 px-2">
      <SidebarLink
        :to="{ name: 'MyWork' }"
        label="My Work"
        :collapsed="collapsed"
      >
        <LucideCircleUser class="size-4" />
      </SidebarLink>
      <SidebarLink
        :to="{ name: 'Projects' }"
        label="Projects"
        :collapsed="collapsed"
      >
        <LucideLayoutGrid class="size-4" />
      </SidebarLink>
    </nav>

    <!-- project list -->
    <div v-if="!collapsed" class="mt-4 flex min-h-0 flex-1 flex-col px-2">
      <div class="flex items-center justify-between px-2 py-1">
        <span class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
          Your projects
        </span>
        <button
          v-if="permissions.canCreateProject"
          class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2"
          title="New project"
          @click="showNewProject = true"
        >
          <LucidePlus class="size-3.5" />
        </button>
      </div>

      <div class="thin-scrollbar min-h-0 flex-1 overflow-y-auto">
        <router-link
          v-for="project in recentProjects"
          :key="project.name"
          :to="{ name: 'Board', params: { project: project.name } }"
          class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
          active-class="bg-surface-gray-3 font-medium text-ink-gray-9"
        >
          <span
            class="size-1.5 shrink-0 rounded-full"
            :class="project.status === 'Open' ? 'bg-blue-500' : 'bg-gray-300'"
          />
          <span class="truncate">{{ project.project_name }}</span>
          <span
            v-if="project.open_tasks"
            class="ml-auto text-xs tabular-nums text-ink-gray-4"
          >
            {{ project.open_tasks }}
          </span>
        </router-link>

        <p
          v-if="!loadingProjects && !recentProjects.length"
          class="px-2 py-2 text-xs text-ink-gray-4"
        >
          No projects yet
        </p>
      </div>
    </div>

    <div v-else class="flex-1" />

    <!-- user -->
    <div class="border-t border-outline-gray-2 p-2">
      <Dropdown :options="userMenu" placement="top-start" class="w-full">
        <button
          class="flex w-full items-center gap-2 rounded px-1.5 py-1.5 hover:bg-surface-gray-2"
        >
          <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
          <span
            v-if="!collapsed"
            class="truncate text-sm font-medium text-ink-gray-8"
          >
            {{ user.full_name }}
          </span>
          <LucideChevronsUpDown
            v-if="!collapsed"
            class="ml-auto size-3.5 text-ink-gray-5"
          />
        </button>
      </Dropdown>
    </div>
  </aside>

  <CreateProjectDialog v-model="showNewProject" @created="onProjectCreated" />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Dropdown } from 'frappe-ui'
import SidebarLink from './SidebarLink.vue'
import CreateProjectDialog from './CreateProjectDialog.vue'
import { logout, permissions, user } from '@/data/session'
import { loadProjects, loadingProjects, projects } from '@/data/projects'

const router = useRouter()
const collapsed = ref(localStorage.getItem('pb:sidebar-collapsed') === '1')
const showNewProject = ref(false)

function toggle() {
  collapsed.value = !collapsed.value
  localStorage.setItem('pb:sidebar-collapsed', collapsed.value ? '1' : '0')
}

// Open projects first - the closed ones stay reachable from the Projects page.
const recentProjects = computed(() =>
  [...projects.value]
    .filter((p) => p.status === 'Open')
    .slice(0, 25),
)

const userMenu = computed(() => [
  {
    label: 'Open in Desk',
    icon: 'external-link',
    onClick: () => window.open('/app/project', '_blank'),
  },
  { label: 'Log out', icon: 'log-out', onClick: logout },
])

function onProjectCreated(name) {
  loadProjects({ force: true })
  router.push({ name: 'Board', params: { project: name } })
}

onMounted(() => loadProjects())
</script>
