<template>
  <FrappeUIProvider>
    <div class="flex h-full w-full overflow-hidden bg-surface-base">
      <AppSidebar />
      <main class="flex min-w-0 flex-1 flex-col overflow-hidden">
        <!-- a grid row (not a percentage height) so every page gets a definite
             height to scroll inside, in every browser -->
        <div class="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)]">
          <router-view />
        </div>
      </main>
      <TaskDetailPanel />
    </div>

    <RunningTimerBar />
    <CommandPalette v-model="paletteOpen" />
    <ShortcutsDialog v-model="showShortcuts" />
    <ConfirmDialog />
  </FrappeUIProvider>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FrappeUIProvider, useColorScheme } from 'frappe-ui'
import AppSidebar from '@/components/AppSidebar.vue'
import CommandPalette from '@/components/CommandPalette.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import RunningTimerBar from '@/components/RunningTimerBar.vue'
import ShortcutsDialog from '@/components/ShortcutsDialog.vue'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'
import { paletteOpen, useShortcuts } from '@/composables/useShortcuts'
import { emit as broadcast, EVENTS, on } from '@/data/bus'
import { closeTask, escapeTargetsPanel } from '@/utils/taskPanel'

const router = useRouter()
const route = useRoute()
const showShortcuts = ref(false)

// restores the saved light/dark/system choice and follows the OS setting
useColorScheme()

let offShortcuts = null
onMounted(() => {
  offShortcuts = on(EVENTS.SHOW_SHORTCUTS, () => (showShortcuts.value = true))
})
onUnmounted(() => offShortcuts?.())

useShortcuts({
  goHome: () => router.push({ name: 'Home' }),
  goMyWork: () => router.push({ name: 'MyWork' }),
  goProjects: () => router.push({ name: 'Projects' }),
  goBoard: () => {
    if (route.params.project)
      router.push({ name: 'Board', params: { project: route.params.project } })
  },
  // The page that owns a create action listens for this.
  create: () => broadcast(EVENTS.CREATE_TASK),
  search: () => broadcast(EVENTS.FOCUS_SEARCH),
  help: () => (showShortcuts.value = true),
  escape: (event) => {
    if (route.query.task && escapeTargetsPanel(event)) closeTask()
  },
})
</script>
