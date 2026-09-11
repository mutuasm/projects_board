<template>
  <div class="no-scrollbar h-full overflow-x-auto overflow-y-hidden">
    <div class="flex h-full min-w-max items-start gap-3 p-4">
      <section
        v-for="status in columns"
        :key="status"
        class="flex h-full w-72 min-w-72 flex-col rounded-lg bg-surface-gray-1"
      >
        <!-- column header -->
        <header class="flex items-center gap-2 px-3 py-2.5">
          <span class="size-2 rounded-full" :class="statusStyle(status).dot" />
          <h2 class="text-xs font-semibold uppercase tracking-wide text-ink-gray-7">
            {{ statusStyle(status).label || status }}
          </h2>
          <span class="text-xs tabular-nums text-ink-gray-5">
            {{ (columnLists[status] || []).length }}
          </span>
          <button
            v-if="permissions.canCreateTask && !terminal.includes(status)"
            class="ml-auto rounded p-1 text-ink-gray-5 hover:bg-surface-gray-3"
            title="Add task to this column"
            @click="quickAdd(status)"
          >
            <LucidePlus class="size-3.5" />
          </button>
        </header>

        <!-- cards -->
        <draggable
          :list="columnLists[status] || []"
          :group="{ name: 'tasks' }"
          item-key="name"
          class="thin-scrollbar flex min-h-16 flex-1 flex-col gap-2 overflow-y-auto px-2 pb-3"
          ghost-class="task-ghost"
          drag-class="task-drag"
          :animation="150"
          @change="(event) => onChange(status, event)"
        >
          <template #item="{ element }">
            <TaskCard :task="element" />
          </template>
          <template #footer>
            <div
              v-if="!(columnLists[status] || []).length"
              class="rounded-lg border border-dashed border-outline-gray-2 py-6 text-center text-xs text-ink-gray-4"
            >
              Drop tasks here
            </div>
          </template>
        </draggable>
      </section>
    </div>

    <CreateTaskDialog
      v-model="showQuickAdd"
      :project="project"
      :default-status="quickAddStatus"
      @created="upsertTask"
    />
  </div>
</template>

<script setup>
import { computed, ref, watchEffect } from 'vue'
import draggable from 'vuedraggable'
import { toast } from 'frappe-ui'
import TaskCard from '@/components/TaskCard.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import api from '@/data/api'
import { groupByStatus, reloadTasks, upsertTask } from '@/data/board'
import { boardStatuses, permissions } from '@/data/session'
import { statusStyle } from '@/utils/constants'

defineProps({ project: { type: String, required: true } })

const terminal = ['Cancelled']
const showQuickAdd = ref(false)
const quickAddStatus = ref('Open')

const columns = computed(() => boardStatuses.value)

/**
 * Sortable mutates the array it is bound to. Holding the columns in a ref (and
 * recomputing them whenever the store changes) lets a dropped card stay put
 * while the server round-trip is in flight, instead of snapping back for a
 * frame the way a plain computed would.
 */
const columnLists = ref({})
watchEffect(() => {
  columnLists.value = groupByStatus(columns.value)
})

function quickAdd(status) {
  quickAddStatus.value = status
  showQuickAdd.value = true
}

/**
 * vuedraggable fires `added` on the destination column. That is the only
 * event we care about - the task's native `status` field is the column.
 */
async function onChange(status, event) {
  const moved = event?.added?.element
  if (!moved || moved.status === status) return

  const previous = moved.status
  moved.status = status // optimistic

  try {
    const updated = await api.moveTask(moved.name, status)
    upsertTask(updated)
  } catch (e) {
    moved.status = previous
    toast.error(
      e?.messages?.join(', ') || e?.message || 'Could not move this task',
    )
    await reloadTasks()
  }
}
</script>
