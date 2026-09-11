<template>
  <div
    class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2 px-5 py-2"
  >
    <div class="relative">
      <LucideSearch
        class="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-ink-gray-4"
      />
      <input
        v-model="filters.search"
        type="text"
        placeholder="Search tasks"
        class="h-7 w-48 rounded border border-outline-gray-2 bg-surface-gray-2 pl-7 pr-2 text-sm text-ink-gray-8 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none focus:ring-0"
      />
    </div>

    <!-- assignee quick filter, Jira style avatar row -->
    <div class="flex items-center gap-1">
      <button
        v-for="member in memberChips"
        :key="member.name"
        class="rounded-full transition-all"
        :class="
          filters.assignee === member.name
            ? 'ring-2 ring-outline-gray-4'
            : 'opacity-70 hover:opacity-100'
        "
        :title="member.full_name"
        @click="toggleAssignee(member.name)"
      >
        <UserAvatar :user="member" size="sm" />
      </button>
      <button
        class="grid size-6 place-items-center rounded-full border border-dashed border-outline-gray-3 text-ink-gray-5"
        :class="filters.assignee === '__unassigned__' ? 'ring-2 ring-outline-gray-4' : ''"
        title="Unassigned"
        @click="toggleAssignee('__unassigned__')"
      >
        <LucideUserX class="size-3" />
      </button>
    </div>

    <Select
      v-model="filters.type"
      :options="typeOptions"
      placeholder="Type"
      size="sm"
      class="w-32"
    />

    <Dropdown :options="priorityOptions" placement="bottom-start">
      <Button variant="ghost" size="sm">
        <template #prefix><LucideSignal class="size-3.5" /></template>
        {{ priorityLabel }}
      </Button>
    </Dropdown>

    <label class="flex items-center gap-1.5 text-sm text-ink-gray-6">
      <input
        v-model="filters.includeCompleted"
        type="checkbox"
        class="rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
      />
      Show done
    </label>

    <Button
      v-if="hasActiveFilters"
      variant="ghost"
      size="sm"
      @click="resetFilters"
    >
      <template #prefix><LucideX class="size-3.5" /></template>
      Clear
    </Button>

    <span class="ml-auto text-xs tabular-nums text-ink-gray-5">
      {{ visibleTasks.length }} of {{ tasks.length }} tasks
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button, Dropdown, Select } from 'frappe-ui'
import UserAvatar from './UserAvatar.vue'
import {
  filters,
  hasActiveFilters,
  members,
  resetFilters,
  tasks,
  visibleTasks,
} from '@/data/board'
import { taskPriorities, taskTypes } from '@/data/session'

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
  taskPriorities.value.map((p) => ({
    label: p,
    onClick: () => togglePriority(p),
  })),
)

const priorityLabel = computed(() =>
  filters.priorities.length
    ? filters.priorities.join(', ')
    : 'Priority',
)

function togglePriority(priority) {
  const index = filters.priorities.indexOf(priority)
  if (index === -1) filters.priorities.push(priority)
  else filters.priorities.splice(index, 1)
}

function toggleAssignee(user) {
  filters.assignee = filters.assignee === user ? null : user
}
</script>
