<template>
  <div class="border-b border-outline-gray-2 px-4 py-2 sm:px-5">
    <!-- phones: one compact row, everything else behind the Filters sheet -->
    <div class="flex items-center gap-2 sm:hidden">
      <TextInput
        ref="mobileSearch"
        v-model="filters.search"
        type="search"
        size="md"
        placeholder="Search tasks"
        class="min-w-0 flex-1"
      >
        <template #prefix><LucideSearch class="size-4 text-ink-gray-5" /></template>
      </TextInput>
      <Button size="md" label="Filters" @click="showSheet = true">
        <template #prefix><LucideSlidersHorizontal class="size-4" /></template>
        <span v-if="activeFilterCount" class="tabular-nums">{{ activeFilterCount }}</span>
      </Button>
    </div>

    <!-- tablet and up: search, people, then one consistent row of filter buttons -->
    <div class="hidden flex-wrap items-center gap-2 sm:flex">
      <TextInput
        ref="desktopSearch"
        v-model="filters.search"
        type="search"
        placeholder="Search tasks"
        class="w-52"
      >
        <template #prefix><LucideSearch class="size-3.5 text-ink-gray-5" /></template>
      </TextInput>

      <!-- assignee quick filter, Jira style avatar row -->
      <div class="no-scrollbar flex max-w-full items-center gap-1 overflow-x-auto">
        <button
          v-for="member in memberChips"
          :key="member.name"
          class="shrink-0 rounded-full transition-all"
          :class="
            filters.assignee === member.name
              ? 'opacity-100 ring-2 ring-outline-gray-4 ring-offset-1'
              : 'opacity-60 hover:opacity-100'
          "
          :title="member.full_name"
          :aria-pressed="filters.assignee === member.name"
          @click="toggleAssignee(member.name)"
        >
          <UserAvatar :user="member" size="sm" />
        </button>
        <button
          class="grid size-6 shrink-0 place-items-center rounded-full border border-dashed border-outline-gray-3 text-ink-gray-5 hover:text-ink-gray-8"
          :class="filters.assignee === '__unassigned__' ? 'ring-2 ring-outline-gray-4 ring-offset-1' : ''"
          title="Unassigned"
          :aria-pressed="filters.assignee === '__unassigned__'"
          @click="toggleAssignee('__unassigned__')"
        >
          <LucideUserX class="size-3" />
        </button>
      </div>

      <span class="mx-1 h-4 w-px shrink-0 bg-outline-gray-2" aria-hidden="true" />

      <Dropdown :options="typeMenu">
        <Button size="sm" :class="filters.type && activeButton">
          <template #prefix><LucideShapes class="size-3.5" /></template>
          {{ filters.type || 'Type' }}
          <template #suffix><LucideChevronDown class="size-3.5 text-ink-gray-5" /></template>
        </Button>
      </Dropdown>

      <Dropdown :options="priorityMenu">
        <Button size="sm" :class="filters.priorities.length && activeButton">
          <template #prefix><LucideSignal class="size-3.5" /></template>
          {{ priorityLabel }}
          <template #suffix><LucideChevronDown class="size-3.5 text-ink-gray-5" /></template>
        </Button>
      </Dropdown>

      <Dropdown v-if="availableTags.length" :options="tagMenu">
        <Button size="sm" :class="filters.tags.length && activeButton">
          <template #prefix><LucideTag class="size-3.5" /></template>
          {{ filters.tags.length ? filters.tags.join(', ') : 'Labels' }}
          <template #suffix><LucideChevronDown class="size-3.5 text-ink-gray-5" /></template>
        </Button>
      </Dropdown>

      <Dropdown :options="swimlaneMenu">
        <Button size="sm" :class="filters.swimlane !== 'none' && activeButton">
          <template #prefix><LucideRows3 class="size-3.5" /></template>
          {{ swimlaneLabel }}
          <template #suffix><LucideChevronDown class="size-3.5 text-ink-gray-5" /></template>
        </Button>
      </Dropdown>

      <Checkbox v-model="filters.includeCompleted" label="Show done" padded />

      <SavedViews />

      <Button v-if="hasActiveFilters" variant="ghost" size="sm" @click="resetFilters">
        <template #prefix><LucideX class="size-3.5" /></template>
        Clear
      </Button>

      <span class="ml-auto text-sm tabular-nums text-ink-gray-5">
        {{ visibleTasks.length }} of {{ tasks.length }}
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
import { Button, Checkbox, Dropdown, TextInput } from 'frappe-ui'
import BoardFilterSheet from './BoardFilterSheet.vue'
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

/** A filter that is doing something reads darker, so you can see why the board is short. */
const activeButton = '!bg-surface-gray-3 !text-ink-gray-9'
const tick = (on) => (on ? 'lucide-check' : '')

const typeMenu = computed(() =>
  typeOptions.value.map((o) => ({
    label: o.label,
    icon: tick((filters.type || '') === o.value),
    onClick: () => (filters.type = o.value),
  })),
)

const priorityMenu = computed(() =>
  taskPriorities.value.map((p) => ({
    label: p,
    icon: tick(filters.priorities.includes(p)),
    onClick: () => togglePriority(p),
  })),
)

const tagMenu = computed(() =>
  availableTags.value.map((tag) => ({
    label: tag,
    icon: tick(filters.tags.includes(tag)),
    onClick: () => toggleTag(tag),
  })),
)

const swimlaneMenu = computed(() => [
  {
    group: 'Swimlanes',
    options: SWIMLANE_OPTIONS.map((o) => ({
      label: o.label,
      icon: tick(filters.swimlane === o.value),
      onClick: () => (filters.swimlane = o.value),
    })),
  },
])

const swimlaneLabel = computed(() =>
  filters.swimlane === 'none'
    ? 'Swimlanes'
    : `By ${SWIMLANE_OPTIONS.find((o) => o.value === filters.swimlane)?.label.toLowerCase()}`,
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
    // frappe-ui's TextInput exposes focus() on its template ref
    const input = isNarrow.value ? mobileSearch.value : desktopSearch.value
    input?.focus()
  })
})
onUnmounted(() => off?.())
</script>
