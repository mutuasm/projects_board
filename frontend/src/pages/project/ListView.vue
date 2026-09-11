<template>
  <div class="thin-scrollbar h-full overflow-y-auto">
    <EmptyState
      v-if="!visibleTasks.length"
      title="No tasks match these filters"
      description="Clear the filters, or create the first task for this project."
    />

    <div v-else class="px-5 py-3">
      <!-- header row -->
      <div
        class="sticky top-0 z-10 grid grid-cols-[minmax(0,1fr)_7rem_7rem_6rem_6rem_5rem] gap-3 border-b border-outline-gray-2 bg-surface-white px-2 py-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5"
      >
        <span>Task</span>
        <span>Status</span>
        <span>Priority</span>
        <span>Due</span>
        <span>Assignees</span>
        <span class="text-right">Weight</span>
      </div>

      <section v-for="group in groups" :key="group.status" class="mt-2">
        <button
          class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left hover:bg-surface-gray-1"
          @click="toggle(group.status)"
        >
          <LucideChevronRight
            class="size-3.5 text-ink-gray-5 transition-transform"
            :class="collapsed.has(group.status) ? '' : 'rotate-90'"
          />
          <span class="size-2 rounded-full" :class="statusStyle(group.status).dot" />
          <span class="text-sm font-medium text-ink-gray-8">
            {{ statusStyle(group.status).label || group.status }}
          </span>
          <span class="text-xs tabular-nums text-ink-gray-5">
            {{ group.tasks.length }}
          </span>
        </button>

        <div v-if="!collapsed.has(group.status)">
          <div
            v-for="task in group.tasks"
            :key="task.name"
            class="grid cursor-pointer grid-cols-[minmax(0,1fr)_7rem_7rem_6rem_6rem_5rem] items-center gap-3 rounded border-b border-outline-gray-1 px-2 py-2 hover:bg-surface-gray-1"
            @click="openTask(task.name)"
          >
            <div class="flex min-w-0 items-center gap-2">
              <LucideFlag
                v-if="task.is_milestone"
                class="size-3.5 shrink-0 text-ink-amber-3"
              />
              <span
                v-if="task.color"
                class="size-2 shrink-0 rounded-full"
                :style="{ backgroundColor: task.color }"
              />
              <span class="truncate text-sm text-ink-gray-8">{{ task.subject }}</span>
              <Badge v-if="task.type" theme="gray" variant="subtle" size="sm">
                {{ task.type }}
              </Badge>
              <span class="shrink-0 font-mono text-xs text-ink-gray-4">
                {{ task.name }}
              </span>
            </div>

            <div @click.stop>
              <StatusPill
                :status="task.status"
                editable
                @change="(s) => setField(task, 'status', s)"
              />
            </div>

            <div @click.stop>
              <PriorityIcon
                :priority="task.priority"
                editable
                show-label
                @change="(p) => setField(task, 'priority', p)"
              />
            </div>

            <span
              class="text-xs"
              :class="
                isOverdue(task.exp_end_date, task.status)
                  ? 'font-medium text-ink-red-3'
                  : 'text-ink-gray-6'
              "
            >
              {{ dueLabel(task.exp_end_date) || '—' }}
            </span>

            <AvatarStack :users="task.assignees || []" :max="2" size="xs" />

            <span class="text-right text-xs tabular-nums text-ink-gray-6">
              {{ task.task_weight ? formatNumber(task.task_weight) : '—' }}
            </span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Badge, toast } from 'frappe-ui'
import AvatarStack from '@/components/AvatarStack.vue'
import EmptyState from '@/components/EmptyState.vue'
import PriorityIcon from '@/components/PriorityIcon.vue'
import StatusPill from '@/components/StatusPill.vue'
import api from '@/data/api'
import { groupByStatus, upsertTask, visibleTasks } from '@/data/board'
import { boardStatuses } from '@/data/session'
import { statusStyle } from '@/utils/constants'
import { dueLabel, formatNumber, isOverdue } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

defineProps({ project: { type: String, required: true } })

const collapsed = ref(new Set())

const groups = computed(() => {
  const byStatus = groupByStatus(boardStatuses.value)
  return boardStatuses.value
    .map((status) => ({ status, tasks: byStatus[status] || [] }))
    .filter((group) => group.tasks.length)
})

function toggle(status) {
  const next = new Set(collapsed.value)
  next.has(status) ? next.delete(status) : next.add(status)
  collapsed.value = next
}

async function setField(task, fieldname, value) {
  const previous = task[fieldname]
  task[fieldname] = value
  try {
    const updated = await api.updateTask(task.name, { [fieldname]: value })
    upsertTask(updated)
  } catch (e) {
    task[fieldname] = previous
    toast.error(e?.messages?.join(', ') || e?.message || 'Update failed')
  }
}
</script>
