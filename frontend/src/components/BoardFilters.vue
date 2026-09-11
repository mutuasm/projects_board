<template>
  <div class="border-b border-outline-gray-2 px-4 py-2 sm:px-5">
    <!-- phones: one compact row, everything else behind the Filters sheet -->
    <div class="flex items-center gap-2 sm:hidden">
      <div class="relative min-w-0 flex-1">
        <LucideSearch
          class="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-ink-gray-4"
        />
        <input
          ref="mobileSearch"
          v-model="filters.search"
          type="text"
          placeholder="Search tasks"
          class="pb-input h-9 w-full pl-7 pr-2"
        />
      </div>
      <button
        class="tap-target flex shrink-0 items-center gap-1.5 rounded border px-2.5 py-1.5 text-sm transition-colors"
        aria-label="Filters"
        :class="
          activeFilterCount
            ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
            : 'border-outline-gray-2 text-ink-gray-7'
        "
        @click="showSheet = true"
      >
        <LucideSlidersHorizontal class="size-4" />
        <span v-if="activeFilterCount" class="tabular-nums">{{ activeFilterCount }}</span>
      </button>
    </div>

    <!-- tablet and up: the controls stay inline -->
    <div class="hidden flex-wrap items-center gap-2 sm:flex">
      <div class="relative">
        <LucideSearch
          class="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-ink-gray-4"
        />
        <input
          ref="desktopSearch"
          v-model="filters.search"
          type="text"
          placeholder="Search tasks"
          class="pb-input h-7 w-48 pl-7 pr-2 text-sm"
        />
      </div>

      <!-- assignee quick filter, Jira style avatar row -->
      <div class="no-scrollbar flex max-w-full items-center gap-1 overflow-x-auto">
        <button
          v-for="member in memberChips"
          :key="member.name"
          class="shrink-0 rounded-full transition-all"
          :class="
            filters.assignee === member.name
              ? 'opacity-100 ring-1 ring-outline-gray-5'
              : 'opacity-50 hover:opacity-100'
          "
          :title="member.full_name"
          @click="toggleAssignee(member.name)"
        >
          <UserAvatar :user="member" size="sm" />
        </button>
        <button
          class="grid size-6 shrink-0 place-items-center rounded-full border border-dashed border-outline-gray-3 text-ink-gray-5"
          :class="filters.assignee === '__unassigned__' ? 'ring-2 ring-outline-gray-4' : ''"
          title="Unassigned"
          @click="toggleAssignee('__unassigned__')"
        >
          <LucideUserX class="size-3" />
        </button>
      </div>

      <div class="w-32 shrink-0">
        <NullableSelect v-model="filters.type" :options="typeOptions" placeholder="Type" />
      </div>

      <Dropdown :options="priorityOptions" placement="bottom-start">
        <Button variant="ghost" size="sm">
          <template #prefix><LucideSignal class="size-3.5" /></template>
          {{ priorityLabel }}
        </Button>
      </Dropdown>

      <Dropdown v-if="availableTags.length" :options="tagOptions" placement="bottom-start">
        <Button variant="ghost" size="sm">
          <template #prefix><LucideTag class="size-3.5" /></template>
          {{ filters.tags.length ? filters.tags.join(', ') : 'Labels' }}
        </Button>
      </Dropdown>

      <div class="w-36 shrink-0">
        <NullableSelect
          v-model="filters.swimlane"
          :options="SWIMLANE_OPTIONS"
          placeholder="Swimlanes"
        />
      </div>

      <label class="flex items-center gap-1.5 text-sm text-ink-gray-6">
        <input
          v-model="filters.includeCompleted"
          type="checkbox"
          class="rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
        />
        Show done
      </label>

      <SavedViews />

      <Button v-if="hasActiveFilters" variant="ghost" size="sm" @click="resetFilters">
        <template #prefix><LucideX class="size-3.5" /></template>
        Clear
      </Button>

      <span class="ml-auto text-xs tabular-nums text-ink-gray-5">
        {{ visibleTasks.length }} of {{ tasks.length }} tasks
      </span>
    </div>

    <BoardFilterSheet
      v-model="showSheet"
      :member-chips="memberChips"
      :type-options="typeOptions"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Button, Dropdown } from 'frappe-ui'
import BoardFilterSheet from './BoardFilterSheet.vue'
import NullableSelect from './NullableSelect.vue'
import SavedViews from './SavedViews.vue'
import UserAvatar from './UserAvatar.vue'
import {
  availableTags,
  filters,
  hasActiveFilters,
  members,
  resetFilters,
  SWIMLANE_OPTIONS,
  tasks,
  visibleTasks,
} from '@/data/board'
import { EVENTS, on } from '@/data/bus'
import { taskPriorities, taskTypes } from '@/data/session'
import { isNarrow } from '@/data/ui'

const showSheet = ref(false)
const mobileSearch = ref(null)
const desktopSearch = ref(null)

/** Project members first; anyone assigned but not a member gets appended. */
const memberChips = computed(() => {
  const seen = new Map(members.value.map((m) => [m.name, m]))
  for (const task of tasks.value) {
    for (const user of task.assignees || []) {
      if (!seen.has(user.name)) seen.set(user.name, user)
    }
  }
  return [...seen.values()].slice(0, 8)
})

const typeOptions = computed(() => [
  { label: 'All types', value: '' },
  ...taskTypes.value.map((t) => ({ label: t, value: t })),
])

const priorityOptions = computed(() =>
  taskPriorities.value.map((p) => ({ label: p, onClick: () => togglePriority(p) })),
)

const tagOptions = computed(() =>
  availableTags.value.map((tag) => ({ label: tag, onClick: () => toggleTag(tag) })),
)

const priorityLabel = computed(() =>
  filters.priorities.length ? filters.priorities.join(', ') : 'Priority',
)

const activeFilterCount = computed(
  () =>
    filters.priorities.length +
    filters.tags.length +
    (filters.assignee ? 1 : 0) +
    (filters.type ? 1 : 0) +
    (filters.swimlane !== 'none' ? 1 : 0) +
    (filters.includeCompleted ? 0 : 1),
)

function togglePriority(priority) {
  const index = filters.priorities.indexOf(priority)
  if (index === -1) filters.priorities.push(priority)
  else filters.priorities.splice(index, 1)
}

function toggleTag(tag) {
  const index = filters.tags.indexOf(tag)
  if (index === -1) filters.tags.push(tag)
  else filters.tags.splice(index, 1)
}

function toggleAssignee(user) {
  filters.assignee = filters.assignee === user ? null : user
}

let off = null
onMounted(() => {
  off = on(EVENTS.FOCUS_SEARCH, () => {
    const el = isNarrow.value ? mobileSearch.value : desktopSearch.value
    el?.focus()
  })
})
onUnmounted(() => off?.())
</script>
