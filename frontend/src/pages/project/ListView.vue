<template>
  <div class="thin-scrollbar h-full overflow-y-auto">
    <EmptyState
      v-if="!visibleTasks.length && !loading"
      title="No tasks match these filters"
      description="Clear the filters, or create the first task for this project."
    />

    <div v-else class="px-4 pb-24 pt-3 sm:px-5 sm:pb-6">
      <div class="mb-2 flex items-center gap-2">
        <span class="hidden text-xs text-ink-gray-5 sm:inline">View</span>
        <TabButtons
          v-model="mode"
          :buttons="[
            { label: 'Tree', value: 'tree' },
            { label: 'Status', value: 'status' },
            { label: 'Flat', value: 'flat' },
          ]"
        />
        <template v-if="mode === 'tree'">
          <Button variant="ghost" size="sm" title="Expand all" @click="expandAll">
            <template #prefix><LucideUnfoldVertical class="size-3.5" /></template>
            <span class="hidden sm:inline">Expand all</span>
          </Button>
          <Button variant="ghost" size="sm" title="Collapse all" @click="collapseAll">
            <template #prefix><LucideFoldVertical class="size-3.5" /></template>
            <span class="hidden sm:inline">Collapse all</span>
          </Button>
        </template>
      </div>

      <!-- header row -->
      <div
        class="sticky top-0 z-10 hidden grid-cols-[1.5rem_minmax(0,1fr)_7rem_7rem_6rem_6rem_5rem] gap-3 border-b border-outline-gray-2 bg-surface-white px-2 py-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5 md:grid"
      >
        <input
          type="checkbox"
          class="size-3.5 rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
          :checked="allSelected"
          :indeterminate.prop="someSelected && !allSelected"
          aria-label="Select all tasks"
          @change="toggleAll"
        />
        <span>Task</span>
        <span>Status</span>
        <span>Priority</span>
        <span>Due</span>
        <span>Assignees</span>
        <span class="text-right">Weight</span>
      </div>

      <!-- tree -->
      <template v-if="mode === 'tree'">
        <TaskRow
          v-for="row in treeRows"
          :key="row.task.name"
          :task="row.task"
          :depth="row.depth"
          :has-children="row.hasChildren"
          :child-count="row.childCount"
          :expanded="!collapsed.has(row.task.name)"
          @toggle="toggle(row.task.name)"
          @field="setField"
        />
      </template>

      <!-- grouped by status, or one flat list -->
      <template v-else>
        <section v-for="group in groups" :key="group.key" class="mt-1">
          <button
            v-if="group.key !== '__flat__'"
            class="flex w-full items-center gap-2 rounded px-2 py-2 text-left hover:bg-surface-gray-1"
            @click="toggle(group.key)"
          >
            <LucideChevronRight
              class="size-3.5 shrink-0 text-ink-gray-5 transition-transform"
              :class="collapsed.has(group.key) ? '' : 'rotate-90'"
            />
            <span class="size-2 shrink-0 rounded-full" :class="group.dot" />
            <span class="truncate text-sm font-medium text-ink-gray-8">{{ group.label }}</span>
            <span class="shrink-0 text-xs tabular-nums text-ink-gray-4">
              {{ group.tasks.length }}
            </span>
          </button>

          <template v-if="!collapsed.has(group.key)">
            <TaskRow
              v-for="task in group.tasks"
              :key="task.name"
              :task="task"
              :depth="group.key === '__flat__' ? 0 : 1"
              @field="setField"
            />
          </template>
        </section>
      </template>
    </div>

    <BulkActionBar />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, TabButtons, toast } from 'frappe-ui'
import BulkActionBar from '@/components/BulkActionBar.vue'
import EmptyState from '@/components/EmptyState.vue'
import TaskRow from '@/components/TaskRow.vue'
import api from '@/data/api'
import {
  buildTaskTree,
  flattenTree,
  loading,
  selection,
  selectMany,
  toggleSelected,
  upsertTask,
  visibleTasks,
} from '@/data/board'
import { boardStatuses } from '@/data/session'
import { sortByPriority, statusStyle } from '@/utils/constants'

defineProps({ project: { type: String, required: true } })

const collapsed = ref(new Set())
const mode = ref(localStorage.getItem('pb:list-mode') || 'tree')
watch(mode, (value) => localStorage.setItem('pb:list-mode', value))

const byPriorityThenDue = (a, b) => {
  // groups float above their siblings so an epic heads its own branch
  if (a.is_group !== b.is_group) return a.is_group ? -1 : 1
  const byPriority = sortByPriority(a, b)
  if (byPriority !== 0) return byPriority
  if (a.exp_end_date && b.exp_end_date) return a.exp_end_date < b.exp_end_date ? -1 : 1
  return a.name < b.name ? -1 : 1
}

const tree = computed(() => buildTaskTree(visibleTasks.value, byPriorityThenDue))
const treeRows = computed(() => flattenTree(tree.value, collapsed.value))

const groups = computed(() => {
  const rows = [...visibleTasks.value].sort(byPriorityThenDue)
  if (mode.value === 'flat') return [{ key: '__flat__', label: '', tasks: rows }]

  const byStatus = new Map(boardStatuses.value.map((s) => [s, []]))
  for (const task of rows) {
    if (!byStatus.has(task.status)) byStatus.set(task.status, [])
    byStatus.get(task.status).push(task)
  }
  return [...byStatus.entries()]
    .filter(([, tasks]) => tasks.length)
    .map(([status, tasks]) => ({
      key: status,
      label: statusStyle(status).label || status,
      dot: statusStyle(status).dot,
      tasks,
    }))
})

const allSelected = computed(
  () => visibleTasks.value.length > 0 && selection.value.size === visibleTasks.value.length,
)
const someSelected = computed(() => selection.value.size > 0)

function toggleAll(event) {
  selectMany(
    visibleTasks.value.map((t) => t.name),
    event.target.checked,
  )
}

function toggle(key) {
  const next = new Set(collapsed.value)
  next.has(key) ? next.delete(key) : next.add(key)
  collapsed.value = next
}

function collapseAll() {
  collapsed.value = new Set(visibleTasks.value.filter((t) => t.is_group).map((t) => t.name))
}

function expandAll() {
  collapsed.value = new Set()
}

async function setField(task, fieldname, value) {
  const previous = task[fieldname]
  task[fieldname] = value
  try {
    upsertTask(await api.updateTask(task.name, { [fieldname]: value }))
  } catch (e) {
    task[fieldname] = previous
    toast.error(e?.messages?.join(', ') || e?.message || 'Update failed')
  }
}

defineExpose({ toggleSelected })
</script>
