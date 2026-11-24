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
      'fixed inset-y-0 left-0 z-50 w-64 lg:static lg:z-auto lg:shadow-none',
      sidebarOpen ? 'translate-x-0 shadow-lg' : '-translate-x-full',
      collapsed ? 'lg:w-14' : 'lg:w-60',
    ]"
  >
    <!-- brand: who this workspace belongs to and who is signed in; the menu
         holds the other apps, the theme and logging out, as in Frappe CRM -->
    <div class="flex items-center gap-1 p-2">
      <div class="min-w-0 flex-1">
        <Dropdown :options="brandMenu" placement="left">
          <template #default="{ open }">
            <button
              class="flex w-full min-w-0 items-center gap-2 rounded-lg p-1.5 text-left transition-colors hover:bg-surface-gray-2"
              :class="[open && '!bg-surface-white shadow-sm', iconsOnly && 'justify-center']"
              :title="iconsOnly ? brand.name : undefined"
            >
              <img
                v-if="brandLogo"
                :src="brandLogo"
                alt=""
                class="size-8 shrink-0 rounded-full object-cover"
                @error="logoFailed = true"
              />
              <span
                v-else
                class="grid size-8 shrink-0 place-items-center rounded-full bg-surface-gray-7 text-sm font-semibold text-ink-white"
              >
                {{ initials(brand.name) }}
              </span>
              <span v-if="!iconsOnly" class="min-w-0 flex-1">
                <span class="block truncate text-base font-medium leading-none text-ink-gray-9">{{ brand.name }}</span>
                <span class="mt-1 block truncate text-sm leading-none text-ink-gray-7">{{ user.full_name }}</span>
              </span>
              <LucideChevronDown v-if="!iconsOnly" class="size-4 shrink-0 text-ink-gray-5" />
            </button>
          </template>
        </Dropdown>
      </div>

      <button
        class="tap-target grid shrink-0 place-items-center rounded p-1 text-ink-gray-5 hover:bg-surface-gray-2 lg:hidden"
        aria-label="Close navigation"
        @click="closeSidebar"
      >
        <LucideX class="size-5" />
      </button>
    </div>

    <!-- primary nav -->
    <nav class="flex flex-col gap-0.5 px-2">
      <SidebarLink
        label="Search"
        :shortcut="searchShortcut"
        :collapsed="iconsOnly"
        @click="openSearch"
      >
        <LucideSearch class="size-4" />
      </SidebarLink>

      <NotificationsBell placement="right-start" class="w-full">
        <template #target="{ togglePopover, isOpen, unread }">
          <SidebarLink
            label="Notifications"
            :badge="unread"
            :active="isOpen"
            :collapsed="iconsOnly"
            @click="togglePopover()"
          >
            <LucideBell class="size-4" />
          </SidebarLink>
        </template>
      </NotificationsBell>

      <SidebarLink :to="{ name: 'Home' }" label="Home" :collapsed="iconsOnly">
        <LucideHome class="size-4" />
      </SidebarLink>
      <SidebarLink :to="{ name: 'MyWork' }" label="My Work" :collapsed="iconsOnly">
        <LucideListChecks class="size-4" />
      </SidebarLink>
      <SidebarLink :to="{ name: 'Projects' }" label="Projects" :collapsed="iconsOnly">
        <LucideFolderKanban class="size-4" />
      </SidebarLink>
    </nav>

    <!-- open projects, collapsible like CRM's view sections -->
    <div v-if="!iconsOnly" class="mt-4 flex min-h-0 flex-1 flex-col px-2">
      <div class="group flex h-7 items-center gap-1 px-2">
        <button
          class="flex min-w-0 flex-1 items-center gap-1.5 text-base text-ink-gray-5 hover:text-ink-gray-7"
          :aria-expanded="showProjects"
          @click="toggleProjects"
        >
          <LucideChevronRight
            class="size-3.5 shrink-0 transition-transform"
            :class="showProjects && 'rotate-90'"
          />
          <span class="truncate">Projects</span>
        </button>
        <button
          v-if="permissions.canCreateProject"
          class="grid place-items-center rounded p-0.5 text-ink-gray-5 opacity-100 hover:bg-surface-gray-3 lg:opacity-0 lg:group-hover:opacity-100 lg:focus-visible:opacity-100"
          title="New project"
          aria-label="New project"
          @click="showNewProject = true"
        >
          <LucidePlus class="size-3.5" />
        </button>
      </div>

      <div
        v-show="showProjects"
        class="thin-scrollbar flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto pb-2"
      >
        <router-link
          v-for="project in recentProjects"
          :key="project.name"
          :to="{ name: 'Board', params: { project: project.name } }"
          class="flex h-7.5 shrink-0 items-center gap-2 rounded px-2 text-sm text-ink-gray-8 transition-colors hover:bg-surface-gray-2"
          :class="
            route.params.project === project.name &&
            '!bg-surface-selected shadow-sm'
          "
        >
          <span class="grid size-4 shrink-0 place-items-center">
            <span
              class="size-2.5 rounded-[3px]"
              :style="{ backgroundColor: projectColor(project.name) }"
            />
          </span>
          <span class="flex-1 truncate">{{ project.project_name }}</span>
          <LucidePauseCircle
            v-if="project.status === 'On hold'"
            class="size-3.5 shrink-0 text-ink-gray-4"
            title="On hold"
          />
          <span v-else-if="project.open_tasks" class="text-xs tabular-nums text-ink-gray-4">
            {{ project.open_tasks }}
          </span>
        </router-link>

        <router-link
          v-if="moreProjects > 0"
          :to="{ name: 'Projects' }"
          class="flex h-7.5 shrink-0 items-center gap-2 rounded px-2 text-sm text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        >
          <span class="size-4 shrink-0" />
          All projects
          <span class="ml-auto text-xs tabular-nums">{{ moreProjects }} more</span>
        </router-link>

        <p
          v-if="!loadingProjects && !recentProjects.length"
          class="px-2 py-1.5 text-sm text-ink-gray-4"
        >
          No open projects
        </p>
      </div>
    </div>

    <div v-else class="flex-1" />

    <!-- help, then collapse -->
    <div class="flex flex-col gap-0.5 p-2">
      <SidebarLink label="Help" :collapsed="iconsOnly" @click="emitBus(EVENTS.SHOW_SHORTCUTS)">
        <LucideCircleHelp class="size-4" />
      </SidebarLink>
      <SidebarLink
        class="hidden lg:flex"
        :label="collapsed ? 'Expand' : 'Collapse'"
        :collapsed="iconsOnly"
        @click="toggleCollapsed"
      >
        <component :is="collapsed ? LucideArrowRightFromLine : LucideArrowLeftToLine" class="size-4" />
      </SidebarLink>
    </div>
  </aside>

  <CreateProjectDialog v-model="showNewProject" @created="onProjectCreated" />
</template>

<script setup>
import { computed, h, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Dropdown, useTheme } from 'frappe-ui'
import SidebarLink from './SidebarLink.vue'
import CreateProjectDialog from './CreateProjectDialog.vue'
import NotificationsBell from './NotificationsBell.vue'
import { brand, logout, permissions, user } from '@/data/session'
import { installedApps, loadInstalledApps } from '@/data/apps'
import { loadProjects, loadingProjects, projects } from '@/data/projects'
import { closeSidebar, isMobile, sidebarOpen } from '@/data/ui'
import { emit as emitBus, EVENTS } from '@/data/bus'
import { batched, onListUpdate } from '@/data/realtime'
import { paletteOpen } from '@/composables/useShortcuts'
import { projectColor } from '@/utils/constants'

import LucideSun from '~icons/lucide/sun'
import LucideMoon from '~icons/lucide/moon'
import LucideSunMoon from '~icons/lucide/sun-moon'
import LucideCheck from '~icons/lucide/check'
import LucideLayoutGrid from '~icons/lucide/layout-grid'
import LucideKeyboard from '~icons/lucide/keyboard'
import LucideLogOut from '~icons/lucide/log-out'
import LucideArrowLeftToLine from '~icons/lucide/arrow-left-to-line'
import LucideArrowRightFromLine from '~icons/lucide/arrow-right-from-line'

const router = useRouter()
const route = useRoute()

function stored(key, fallback) {
  try {
    return localStorage.getItem(key) ?? fallback
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

const collapsed = ref(stored('pb:sidebar-collapsed', '0') === '1')
const showProjects = ref(stored('pb:sidebar-projects', '1') === '1')
const showNewProject = ref(false)
const logoFailed = ref(false)

/** The drawer is always full width; only the desktop rail collapses. */
const iconsOnly = computed(() => collapsed.value && !isMobile.value)

function toggleCollapsed() {
  collapsed.value = !collapsed.value
  store('pb:sidebar-collapsed', collapsed.value ? '1' : '0')
}

function toggleProjects() {
  showProjects.value = !showProjects.value
  store('pb:sidebar-projects', showProjects.value ? '1' : '0')
}

const searchShortcut = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘K' : 'Ctrl K'

function openSearch() {
  closeSidebar()
  paletteOpen.value = true
}

const brandLogo = computed(() => (logoFailed.value ? null : brand.value.logo))
watch(() => brand.value.logo, () => (logoFailed.value = false))

function initials(name) {
  return (name || 'P')
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() || '')
    .join('')
}

// Open and paused projects, most recently touched first - the closed ones stay
// reachable from the Projects page.
/** The sidebar is for getting around, not a directory: your projects first, a short list. */
const SIDEBAR_PROJECTS = 10
const openProjects = computed(() =>
  projects.value.filter((p) => ['Open', 'On hold'].includes(p.status)),
)
const recentProjects = computed(() => {
  const me = user.value?.name
  const mine = (p) => (p.members || []).some((m) => m.name === me)
  return [...openProjects.value.filter(mine), ...openProjects.value.filter((p) => !mine(p))].slice(
    0,
    SIDEBAR_PROJECTS,
  )
})
const moreProjects = computed(() => openProjects.value.length - recentProjects.value.length)

const { currentTheme, setTheme } = useTheme()

/** A dropdown icon from an image URL: the apps menu shows each app's logo. */
function logoIcon(src) {
  return (_, { attrs }) =>
    h('img', { ...attrs, src, alt: '', class: [attrs.class, 'rounded object-contain'] })
}

// Frappe's own list of the site's apps - the desk's apps screen reads the same.
const appsMenu = computed(() => [
  {
    label: 'Desk',
    icon: logoIcon('/assets/frappe/images/frappe-framework-logo.svg'),
    onClick: () => (window.location.href = '/desk'),
  },
  ...(installedApps.data || [])
    .filter((app) => app.route && app.name !== 'project_board')
    .map((app) => ({
      label: app.title || app.name,
      icon: app.logo ? logoIcon(app.logo) : LucideLayoutGrid,
      onClick: () => (window.location.href = app.route),
    })),
])

const themeMenu = computed(() =>
  [
    { value: 'light', label: 'Light', icon: LucideSun },
    { value: 'dark', label: 'Dark', icon: LucideMoon },
    { value: 'system', label: 'System', icon: LucideSunMoon },
  ].map((theme) => ({
    label: theme.label,
    icon: currentTheme.value === theme.value ? LucideCheck : theme.icon,
    onClick: () => setTheme(theme.value),
  })),
)

const brandMenu = computed(() => [
  {
    group: 'App',
    hideLabel: true,
    items: [
      { label: 'Apps', icon: LucideLayoutGrid, submenu: appsMenu.value },
      {
        label: 'Theme',
        icon: { light: LucideSun, dark: LucideMoon }[currentTheme.value] || LucideSunMoon,
        submenu: themeMenu.value,
      },
      {
        label: 'Keyboard shortcuts',
        icon: LucideKeyboard,
        onClick: () => emitBus(EVENTS.SHOW_SHORTCUTS),
      },
    ],
  },
  {
    group: 'Account',
    hideLabel: true,
    items: [{ label: 'Log out', icon: LucideLogOut, onClick: logout }],
  },
])

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
  loadInstalledApps()
  stopLive = [
    onListUpdate('Project', () => refreshProjects()),
    onListUpdate('Task', () => refreshProjects()),
  ]
})
onUnmounted(() => stopLive.forEach((stop) => stop()))
</script>
