<template>
  <div
    class="pb-card group cursor-pointer p-2.5"
    :class="selected ? 'pb-card-selected' : ''"
    @click="openTask(task.name)"
  >
    <div class="flex items-start gap-2">
      <LucideFlag
        v-if="task.is_milestone"
        class="mt-0.5 size-3.5 shrink-0 text-ink-amber-5"
      />
      <Tooltip v-if="task.auto_repeat" text="Repeating task">
        <LucideRepeat class="mt-0.5 size-3.5 shrink-0 text-ink-gray-5" />
      </Tooltip>
      <p class="flex-1 text-sm leading-snug text-ink-gray-9">{{ task.subject }}</p>
      <Tooltip v-if="isTiming" text="Timer running on this task">
        <span class="relative mt-1 flex size-2 shrink-0">
          <span
            class="absolute inline-flex size-full animate-ping rounded-full bg-red-400 opacity-75"
          />
          <span class="relative inline-flex size-2 rounded-full bg-red-500" />
        </span>
      </Tooltip>
    </div>

    <!-- labels stay as plain text, not another row of pills -->
    <p v-if="task.tags?.length" class="mt-1.5 truncate text-[11px] text-ink-gray-5">
      {{ task.tags.join(' · ') }}
    </p>

    <!-- one quiet meta line: where it belongs, then only what's unusual -->
    <div class="mt-2.5 flex min-w-0 items-center gap-2">
      <button
        v-if="task.epic"
        class="flex min-w-0 items-center gap-1.5 text-xs text-ink-gray-5 hover:text-ink-gray-8"
        :title="`Show only ${task.epic.subject}`"
        @click.stop="$emit('filter-epic', task.epic.name)"
      >
        <span
          class="size-2 shrink-0 rounded-[3px]"
          :style="{ backgroundColor: task.epic.color || '#9ca3af' }"
        />
        <span class="truncate">{{ task.epic.subject }}</span>
      </button>

      <Tooltip v-if="task.type" :text="`Type: ${task.type}`">
        <span
          class="shrink-0 text-[11px] font-medium uppercase tracking-wide"
          :class="typeStyle.text"
        >
          {{ typeStyle.short }}
        </span>
      </Tooltip>

      <PriorityIcon v-if="isNotablePriority(task.priority)" :priority="task.priority" />

      <Tooltip
        v-if="task.status === 'Pending Review' && task.review_date"
        :text="`Review by ${formatDate(task.review_date)}`"
      >
        <span
          class="inline-flex shrink-0 items-center gap-0.5 text-xs"
          :class="reviewLate ? 'font-medium text-ink-red-5' : 'text-ink-amber-5'"
        >
          <LucideClipboardCheck class="size-3" />
          {{ dueLabel(task.review_date) }}
        </span>
      </Tooltip>

      <Tooltip v-if="task.is_blocked" :text="blockedLabel">
        <LucideLock class="size-3.5 shrink-0 text-ink-amber-5" />
      </Tooltip>

      <span
        v-if="task.exp_end_date"
        class="shrink-0 text-xs"
        :class="overdue ? 'font-medium text-ink-red-5' : 'text-ink-gray-5'"
      >
        {{ dueLabel(task.exp_end_date) }}
      </span>

      <span
        v-if="task.comment_count"
        class="inline-flex shrink-0 items-center gap-0.5 text-xs text-ink-gray-5"
      >
        <LucideMessageSquare class="size-3" />
        {{ task.comment_count }}
      </span>

      <span
        v-if="task.task_weight"
        class="shrink-0 rounded-4 bg-surface-gray-2 px-1 text-[11px] tabular-nums text-ink-gray-6"
        :title="`Weight ${task.task_weight}`"
      >
        {{ formatNumber(task.task_weight) }}
      </span>

      <span class="ml-auto shrink-0">
        <AvatarStack :users="task.assignees || []" :max="2" size="xs" />
      </span>
    </div>

    <!-- progress on partially-done work -->
    <div
      v-if="task.progress > 0 && task.progress < 100"
      class="mt-2 h-0.5 w-full overflow-hidden rounded-full bg-surface-gray-2"
    >
      <div
        class="h-full rounded-full bg-surface-blue-6"
        :style="{ width: `${task.progress}%` }"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'
import AvatarStack from './AvatarStack.vue'
import PriorityIcon from './PriorityIcon.vue'
import { isNotablePriority, taskTypeStyle } from '@/utils/constants'
import { dayjs, dueLabel, formatDate, formatNumber, isOverdue } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'
import { isTimingTask } from '@/data/timer'

const props = defineProps({
  task: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['filter-epic'])

const overdue = computed(() => isOverdue(props.task.exp_end_date, props.task.status))
const isTiming = computed(() => isTimingTask(props.task.name))
const typeStyle = computed(() => taskTypeStyle(props.task.type))
const reviewLate = computed(
  () => props.task.review_date && dayjs(props.task.review_date).isBefore(dayjs().startOf('day')),
)
const blockedLabel = computed(() => `Waiting on ${(props.task.blocked_by || []).join(', ')}`)
</script>
