<template>
  <!-- scrim: only ever visible while the drawer is open on small screens -->
  <Transition
    enter-active-class="transition-opacity duration-150"
    leave-active-class="transition-opacity duration-150"
    enter-from-class="opacity-0"
    leave-to-class="opacity-0"
  >
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-black/30 lg:hidden"
      @click="closeSidebar"
    />
  </Transition>

  <aside
    class="flex h-full shrink-0 flex-col border-r border-outline-gray-2 bg-surface-menu-bar pb-safe-bottom pl-safe-left pt-safe-top transition-transform duration-200 lg:translate-x-0 lg:transition-all"
    :class="[
      // phone/tablet: an overlay drawer that slides in from the left
      'fixed inset-y-0 left-0 z-50 w-72 lg:static lg:z-auto lg:shadow-none',
      sidebarOpen ? 'translate-x-0 shadow-lg' : '-translate-x-full',
      collapsed ? 'lg:w-16' : 'lg:w-64',
    ]"
  >
    <!-- brand -->
    <div class="flex items-center gap-2 px-4 pb-4 pt-4" :class="iconsOnly ? 'justify-center px-2' : ''">
      <router-link
        :to="{ name: 'MyWork' }"
        class="truncate text-[19px] font-semibold tracking-[-0.02em] text-ink-gray-9"
        :title="iconsOnly ? 'Project Board' : undefined"
      >
        {{ iconsOnly ? 'P' : 'Project Board' }}
      </router-link>

      <!-- close on mobile, collapse on desktop -->
      <button
        class="tap-target ml-auto grid place-items-center rounded p-1 text-ink-gray-5 hover:bg-surface-gray-2 lg:hidden"
        aria-label="Close navigation"
        @click="closeSidebar"
      >
        <LucideX class="size-5" />
      </button>
      <button
        v-if="!iconsOnly"
        class="ml-auto hidden rounded p-1 text-ink-gray-5 hover:bg-surface-gray-2 lg:block"
        title="Collapse"
        @click="toggleCollapsed"
      >
        <LucidePanelLeft class="size-4" />
      </button>
    </div>

    <!-- primary nav -->
    <nav class="flex flex-col gap-1 px-3" :class="iconsOnly ? 'px-2' : ''">
      <button
        v-if="iconsOnly"
        class="mb-1 hidden place-items-center rounded-lg py-2 text-ink-gray-5 hover:bg-surface-gray-2 lg:grid"
        title="Expand"
        @click="toggleCollapsed"
      >
        <LucidePanelLeft class="size-4" />
      </button>
      <SidebarLink :to="{ name: 'MyWork' }" label="My Work" :collapsed="iconsOnly">
        <LucideLayoutDashboard class="size-[18px]" />
      </SidebarLink>
      <SidebarLink :to="{ name: 'Projects' }" label="Projects" :collapsed="iconsOnly">
        <LucideFolderKanban class="size-[18px]" />
      </SidebarLink>
    </nav>

    <!-- project list -->
    <div
      v-if="!iconsOnly"
      class="mt-5 flex min-h-0 flex-1 flex-col border-t border-outline-gray-2 px-3 pt-4"
    >
      <div class="flex items-center justify-between px-2.5 pb-1.5">
        <span class="text-[15px] text-ink-gray-6">Projects</span>
        <button
          v-if="permissions.canCreateProject"
          class="tap-target grid place-items-center rounded p-1 text-ink-gray-6 hover:bg-surface-gray-2"
          title="New project"
          @click="showNewProject = true"
        >
          <LucidePlus class="size-4" />
        </button>
      </div>

      <div class="thin-scrollbar flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto">
        <router-link
          v-for="project in recentProjects"
          :key="project.name"
          :to="{ name: 'Board', params: { project: project.name } }"
          class="flex items-center gap-3 rounded-lg border border-transparent px-2.5 py-2 text-[15px] text-ink-gray-7 hover:bg-surface-gray-2"
          :class="
            route.params.project === project.name
              ? '!border-outline-gray-2 !bg-surface-white font-medium text-ink-gray-9 shadow-sm'
              : ''
          "
        >
          <span
            class="size-3.5 shrink-0 rounded-[4px]"
            :style="{ backgroundColor: projectColor(project.name) }"
          />
          <span class="truncate">{{ project.project_name }}</span>
          <LucidePauseCircle
            v-if="project.status === 'On hold'"
            class="ml-auto size-3.5 shrink-0 text-ink-gray-4"
            title="On hold"
          />
          <span
            v-else-if="project.open_tasks"
            class="ml-auto text-xs tabular-nums text-ink-gray-4"
          >
            {{ project.open_tasks }}
          </span>
        </router-link>

        <p
          v-if="!loadingProjects && !recentProjects.length"
          class="px-2.5 py-2 text-xs text-ink-gray-4"
        >
          No projects yet
        </p>
      </div>
    </div>

    <div v-else class="flex-1" />

    <!-- secondary links, then the user -->
    <div class="flex flex-col gap-0.5 px-3 pb-2" :class="iconsOnly ? 'px-2' : ''">
      <button
        class="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[15px] text-ink-gray-7 hover:bg-surface-gray-2"
        :title="iconsOnly ? 'Keyboard shortcuts' : undefined"
        @click="emitBus(EVENTS.SHOW_SHORTCUTS)"
      >
        <LucideKeyboard class="size-[18px] shrink-0 text-ink-gray-6" />
        <span v-if="!iconsOnly">Shortcuts</span>
        <kbd
          v-if="!iconsOnly"
          class="ml-auto rounded-md bg-surface-gray-3 px-1.5 text-xs text-ink-gray-6"
        >?</kbd>
      </button>
      <button
        class="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[15px] text-ink-gray-7 hover:bg-surface-gray-2"
        :title="iconsOnly ? `Theme: ${themeLabel}` : undefined"
        @click="cycleTheme"
      >
        <component :is="themeIcon" class="size-[18px] shrink-0 text-ink-gray-6" />
        <span v-if="!iconsOnly">Theme</span>
        <span v-if="!iconsOnly" class="ml-auto text-xs text-ink-gray-5">{{ themeLabel }}</span>
      </button>
    </div>

    <div class="border-t border-outline-gray-2 p-2">
      <Dropdown :options="userMenu" placement="top-start" class="w-full">
        <button
          class="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 hover:bg-surface-gray-2"
        >
          <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
          <span v-if="!iconsOnly" class="truncate text-sm font-medium text-ink-gray-8">
            {{ user.full_name }}
          </span>
          <LucideChevronsUpDown
            v-if="!iconsOnly"
            class="ml-auto size-3.5 text-ink-gray-5"
          />
        </button>
      </Dropdown>
    </div>
  </aside>

  <CreateProjectDialog v-model="showNewProject" @created="onProjectCreated" />
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Dropdown, useTheme } from 'frappe-ui'
import SidebarLink from './SidebarLink.vue'
import CreateProjectDialog from './CreateProjectDialog.vue'
import { logout, permissions, user } from '@/data/session'
import { loadProjects, loadingProjects, projects } from '@/data/projects'
import { closeSidebar, isMobile, sidebarOpen } from '@/data/ui'
import { emit as emitBus, EVENTS } from '@/data/bus'
import { batched, onListUpdate } from '@/data/realtime'
import { projectColor } from '@/utils/constants'

import LucideSun from '~icons/lucide/sun'
import LucideMoon from '~icons/lucide/moon'
import LucideSunMoon from '~icons/lucide/sun-moon'

const router = useRouter()
const route = useRoute()
const collapsed = ref(localStorage.getItem('pb:sidebar-collapsed') === '1')
const showNewProject = ref(false)

/** The drawer is always full width; only the desktop rail collapses. */
const iconsOnly = computed(() => collapsed.value && !isMobile.value)

function toggleCollapsed() {
  collapsed.value = !collapsed.value
  localStorage.setItem('pb:sidebar-collapsed', collapsed.value ? '1' : '0')
}

// Open and paused projects, most recently touched first - the closed ones stay
// reachable from the Projects page.
const recentProjects = computed(() =>
  projects.value.filter((p) => ['Open', 'On hold'].includes(p.status)).slice(0, 25),
)

const { currentTheme, setTheme } = useTheme()

const userMenu = computed(() => [
  { label: 'Go to Desk', icon: 'monitor', onClick: () => (window.location.href = '/app') },
  { label: 'Log out', icon: 'log-out', onClick: logout },
])

const themeIcon = computed(
  () => ({ light: LucideSun, dark: LucideMoon }[currentTheme.value] || LucideSunMoon),
)

const themeLabel = computed(
  () => ({ light: 'Light', dark: 'Dark', system: 'System' })[currentTheme.value] || 'System',
)

/** light -> dark -> system, the usual three-state cycle. */
function cycleTheme() {
  const next = { light: 'dark', dark: 'system', system: 'light' }[currentTheme.value] || 'dark'
  setTheme(next)
}

function onProjectCreated(name) {
  loadProjects({ force: true })
  closeSidebar()
  router.push({ name: 'Board', params: { project: name } })
}

// Navigating away is the drawer's cue to get out of the way.
watch(() => route.fullPath, closeSidebar)

// Lock background scrolling while the drawer covers the page.
watch(sidebarOpen, (open) => {
  document.body.style.overflow = open && isMobile.value ? 'hidden' : ''
})
watch(isMobile, (mobile) => {
  if (!mobile) {
    closeSidebar()
    document.body.style.overflow = ''
  }
})

// New, renamed, paused or closed projects - and open-task counts - follow along
// live. Task saves are frequent, so those wait for a quiet moment.
const refreshProjects = batched(() => loadProjects({ force: true }), 1500)
let stopLive = []
onMounted(() => {
  loadProjects()
  stopLive = [
    onListUpdate('Project', () => refreshProjects()),
    onListUpdate('Task', () => refreshProjects()),
  ]
})
onUnmounted(() => stopLive.forEach((stop) => stop()))
</script>
