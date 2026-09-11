<template>
  <div class="flex flex-col gap-1.5">
    <div
      v-for="dep in dependencies"
      :key="dep.name"
      class="group flex items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-1"
    >
      <span class="size-1.5 shrink-0 rounded-full" :class="statusStyle(dep.status).dot" />
      <button
        class="min-w-0 flex-1 truncate text-left text-sm text-ink-gray-8 hover:underline"
        @click="$emit('open', dep.name)"
      >
        {{ dep.subject }}
      </button>
      <Badge
        v-if="!['Completed', 'Cancelled'].includes(dep.status)"
        theme="orange"
        variant="subtle"
        size="sm"
      >
        blocking
      </Badge>
      <button
        v-if="!readonly"
        class="text-ink-gray-4 opacity-0 transition-opacity hover:text-ink-red-3 group-hover:opacity-100"
        :aria-label="`Remove dependency ${dep.subject}`"
        @click="remove(dep.name)"
      >
        <LucideX class="size-3.5" />
      </button>
    </div>

    <Autocomplete
      v-if="!readonly"
      :options="options"
      :model-value="null"
      :loading="searching"
      placeholder="Search tasks"
      @update:model-value="onPick"
      @update:query="onQuery"
    >
      <template #target="{ togglePopover }">
        <button
          class="flex w-fit items-center gap-1 rounded border border-dashed border-outline-gray-3 px-1.5 py-1 text-xs text-ink-gray-6 hover:border-outline-gray-4 hover:text-ink-gray-8"
          @click="togglePopover()"
        >
          <LucidePlus class="size-3" />
          Add blocker
        </button>
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Autocomplete, Badge } from 'frappe-ui'
import api from '@/data/api'
import { statusStyle } from '@/utils/constants'

const props = defineProps({
  /** Array of { name, subject, status, priority }. */
  dependencies: { type: Array, default: () => [] },
  task: { type: String, required: true },
  project: { type: String, default: null },
  readonly: { type: Boolean, default: false },
})
const emit = defineEmits(['change', 'open'])

const results = ref([])
const searching = ref(false)
let searchToken = 0

const options = computed(() =>
  results.value.map((t) => ({ label: t.subject, value: t.name, description: t.status })),
)

async function onQuery(txt) {
  const token = ++searchToken
  searching.value = true
  try {
    const rows = await api.searchTasks({
      project: props.project,
      txt,
      // never let a task depend on itself or duplicate an existing blocker
      exclude: [props.task, ...props.dependencies.map((d) => d.name)],
      limit: 15,
    })
    if (token === searchToken) results.value = rows || []
  } finally {
    if (token === searchToken) searching.value = false
  }
}

function onPick(option) {
  if (!option) return
  const value = typeof option === 'string' ? option : option.value
  emit('change', [...props.dependencies.map((d) => d.name), value])
}

function remove(name) {
  emit(
    'change',
    props.dependencies.map((d) => d.name).filter((n) => n !== name),
  )
}
</script>
