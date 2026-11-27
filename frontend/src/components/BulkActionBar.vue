<template>
  <Transition
    enter-active-class="transition-all duration-150"
    leave-active-class="transition-all duration-150"
    enter-from-class="translate-y-4 opacity-0"
    leave-to-class="translate-y-4 opacity-0"
  >
    <div
      v-if="count"
      class="fixed bottom-4 left-1/2 z-30 flex max-w-[95vw] -translate-x-1/2 flex-wrap items-center gap-2 rounded-full border border-outline-gray-3 bg-surface-base px-3 py-2 shadow-md"
      style="margin-bottom: env(safe-area-inset-bottom)"
    >
      <span class="px-1 text-sm-medium tabular-nums text-ink-gray-8">
        {{ count }} selected
      </span>

      <Dropdown :options="statusOptions" side="top">
        <Button variant="ghost" size="sm" :loading="busy === 'status'">Status</Button>
      </Dropdown>
      <Dropdown :options="priorityOptions" side="top">
        <Button variant="ghost" size="sm" :loading="busy === 'priority'">Priority</Button>
      </Dropdown>
      <Button variant="ghost" size="sm" @click="showAssign = true">Assign</Button>

      <span class="h-4 w-px bg-outline-gray-2" />

      <Button
        variant="ghost"
        size="sm"
        theme="red"
        :loading="busy === 'delete'"
        @click="remove"
      >
        <template #prefix><LucideTrash2 class="size-3.5" /></template>
        Delete
      </Button>
      <Button variant="ghost" size="sm" label="Clear selection" @click="clearSelection">
        <template #icon><LucideX class="size-4" /></template>
      </Button>
    </div>
  </Transition>

  <Dialog v-model="showAssign" :title="`Assign ${count} tasks`" size="sm">
    <template #default>
      <p class="mb-2 text-xs text-ink-gray-5">
        This replaces the current assignees on every selected task.
      </p>
      <AssigneeSelect v-model="assignees" />
    </template>
    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button @click="showAssign = false">Cancel</Button>
        <Button variant="solid" :loading="busy === 'assign'" @click="applyAssignees">
          Assign
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Dialog, Dropdown, toast } from 'frappe-ui'
import AssigneeSelect from './AssigneeSelect.vue'
import api from '@/data/api'
import { clearSelection, removeTask, selection, upsertTask } from '@/data/board'
import { boardStatuses, taskPriorities } from '@/data/session'
import { statusStyle } from '@/utils/constants'
import { confirmAction } from '@/utils/confirm'

const busy = ref(null)
const showAssign = ref(false)
const assignees = ref([])

const count = computed(() => selection.value.size)
const names = computed(() => [...selection.value])

const statusOptions = computed(() =>
  boardStatuses.value.map((s) => ({
    label: statusStyle(s).label || s,
    onClick: () => apply('status', { status: s }),
  })),
)

const priorityOptions = computed(() =>
  taskPriorities.value.map((p) => ({
    label: p,
    onClick: () => apply('priority', { priority: p }),
  })),
)

/** Reports partial failures rather than pretending the whole batch worked. */
function report(result, verb) {
  for (const row of result.updated || []) upsertTask(row)

  const failed = result.failed || []
  if (failed.length) {
    toast.error(
      `${failed.length} of ${count.value} could not be ${verb}: ${failed[0].error}`,
    )
  } else {
    toast.success(`${count.value} tasks ${verb}`)
    clearSelection()
  }
}

async function apply(kind, values) {
  busy.value = kind
  try {
    report(await api.bulkUpdateTasks(names.value, values), 'updated')
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Bulk update failed')
  } finally {
    busy.value = null
  }
}

async function applyAssignees() {
  busy.value = 'assign'
  try {
    report(await api.bulkUpdateTasks(names.value, { assignees: assignees.value }), 'updated')
    showAssign.value = false
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Bulk assign failed')
  } finally {
    busy.value = null
  }
}

function remove() {
  confirmAction({
    title: `Delete ${count.value} tasks?`,
    message: "The selected tasks will be deleted. This can't be undone.",
    label: 'Delete',
    onConfirm: deleteSelected,
  })
}

async function deleteSelected() {
  busy.value = 'delete'
  try {
    const result = await api.bulkDeleteTasks(names.value)
    for (const name of result.deleted || []) removeTask(name)
    if (result.failed?.length) {
      toast.error(`${result.failed.length} could not be deleted: ${result.failed[0].error}`)
    } else {
      toast.success(`${result.deleted.length} tasks deleted`)
    }
    clearSelection()
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Bulk delete failed')
  } finally {
    busy.value = null
  }
}
</script>
