<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover }">
      <button
        class="grid size-9 shrink-0 place-items-center rounded-lg border border-outline-gray-2 text-ink-gray-7 transition-colors hover:bg-surface-gray-2"
        aria-label="Switch app"
        title="Switch app"
        @click="open(togglePopover)"
      >
        <LucideLayoutGrid class="size-4" />
      </button>
    </template>

    <template #body-main>
      <div class="w-[calc(100vw-2rem)] p-2 sm:w-80">
        <p class="px-2 pb-2 pt-1 text-xs font-medium text-ink-gray-5">Apps</p>

        <div v-if="installedApps.loading && !apps.length" class="grid grid-cols-3 gap-1">
          <div v-for="n in 3" :key="n" class="flex flex-col items-center gap-2 p-3">
            <div class="size-10 animate-pulse rounded-xl bg-surface-gray-2" />
            <div class="h-2.5 w-14 animate-pulse rounded bg-surface-gray-2" />
          </div>
        </div>

        <p v-else-if="installedApps.error" class="px-2 pb-2 text-sm text-ink-gray-6">
          Couldn't load the apps.
          <button class="font-medium text-ink-gray-8 underline" @click="installedApps.fetch()">
            Try again
          </button>
        </p>

        <div v-else class="grid grid-cols-3 gap-1">
          <a
            v-for="app in apps"
            :key="app.name"
            :href="app.route"
            class="relative flex flex-col items-center gap-2 rounded-lg p-3 text-center transition-colors hover:bg-surface-gray-2"
            :class="app.current && 'bg-surface-gray-2'"
            :aria-current="app.current ? 'page' : undefined"
          >
            <img
              v-if="app.logo && !failedLogos.has(app.name)"
              :src="app.logo"
              alt=""
              class="size-10 rounded-xl object-contain"
              @error="failedLogos.add(app.name)"
            />
            <span
              v-else
              class="grid size-10 place-items-center rounded-xl bg-surface-gray-3 text-base font-semibold text-ink-gray-7"
            >
              {{ (app.title || app.name).charAt(0).toUpperCase() }}
            </span>
            <span class="line-clamp-2 text-xs font-medium leading-tight text-ink-gray-8">
              {{ app.title || app.name }}
            </span>
          </a>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { Popover } from 'frappe-ui'
import { installedApps, loadInstalledApps } from '@/data/apps'

const failedLogos = reactive(new Set())

const apps = computed(() =>
  (installedApps.data || [])
    .filter((app) => app.route)
    .map((app) => ({ ...app, current: app.name === 'project_board' })),
)

function open(togglePopover) {
  loadInstalledApps()
  togglePopover()
}
</script>
