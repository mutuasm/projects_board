<template>
  <Dialog v-model="show" :options="{ title: 'Filters', size: 'md' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <section>
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            Assignee
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="member in memberChips"
              :key="member.name"
              class="flex items-center gap-1.5 rounded-full border py-1 pl-1 pr-2.5 text-sm transition-colors"
              :class="
                filters.assignee === member.name
                  ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7'
              "
              @click="toggleAssignee(member.name)"
            >
              <UserAvatar :user="member" size="sm" />
              <span class="max-w-28 truncate">{{ member.full_name }}</span>
            </button>
            <button
              class="flex items-center gap-1.5 rounded-full border py-1 pl-2 pr-2.5 text-sm transition-colors"
              :class="
                filters.assignee === '__unassigned__'
                  ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7'
              "
              @click="toggleAssignee('__unassigned__')"
            >
              <LucideUserX class="size-4" />
              Unassigned
            </button>
          </div>
        </section>

        <section>
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            Priority
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="priority in taskPriorities"
              :key="priority"
              class="rounded-full border px-3 py-1.5 text-sm transition-colors"
              :class="
                filters.priorities.includes(priority)
                  ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7'
              "
              @click="togglePriority(priority)"
            >
              {{ priority }}
            </button>
          </div>
        </section>

        <section v-if="availableTags.length">
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            Labels
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="tag in availableTags"
              :key="tag"
              class="rounded-full border px-3 py-1.5 text-sm transition-colors"
              :class="
                filters.tags.includes(tag)
                  ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7'
              "
              @click="toggleTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </section>

        <section>
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            Type
          </p>
          <NullableSelect v-model="filters.type" :options="typeOptions" />
        </section>

        <section v-if="epics.length">
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            Epic
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="epic in epics"
              :key="epic.name"
              class="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors"
              :class="
                filters.epic === epic.name
                  ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7'
              "
              @click="filters.epic = filters.epic === epic.name ? null : epic.name"
            >
              <span
                class="size-2 rounded-[3px]"
                :style="{ backgroundColor: epic.color || '#9ca3af' }"
              />
              {{ epic.subject }}
            </button>
          </div>
        </section>

        <section>
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            Swimlanes
          </p>
          <NullableSelect v-model="filters.swimlane" :options="SWIMLANE_OPTIONS" />
        </section>

        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <input
            v-model="filters.includeCompleted"
            type="checkbox"
            class="size-4 rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
          />
          Show done tasks
        </label>
      </div>
    </template>

    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
        <Button :disabled="!hasActiveFilters" @click="resetFilters">
          Clear all
        </Button>
        <Button variant="solid" @click="show = false">
          Show {{ visibleTasks.length }} tasks
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Button, Dialog } from 'frappe-ui'
import NullableSelect from './NullableSelect.vue'
import UserAvatar from './UserAvatar.vue'
import {
  availableTags,
  epics,
  filters,
  hasActiveFilters,
  resetFilters,
  SWIMLANE_OPTIONS,
  visibleTasks,
} from '@/data/board'
import { taskPriorities } from '@/data/session'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  memberChips: { type: Array, default: () => [] },
  typeOptions: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

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
</script>
