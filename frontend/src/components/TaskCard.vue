<template>
  <div
    class="pb-card group cursor-pointer p-2.5"
    :class="selected ? 'pb-card-selected' : ''"
    @click="openTask(task.name)"
  >
    <!-- epic chip: a colour swatch plus the parent's name, Jira style -->
    <button
      v-if="task.epic"
      class="mb-1.5 flex max-w-full items-center gap-1.5 text-[11px] font-medium text-ink-gray-6 hover:text-ink-gray-8"
      @click.stop="$emit('filter-epic', task.epic.name)"
    >
      <span
        class="size-2 shrink-0 rounded-[3px]"
        :style="{ backgroundColor: task.epic.color || '#9ca3af' }"
      />
      <span class="truncate">{{ task.epic.subject }}</span>
    </button>

    <div class="flex items-start gap-2">
      <LucideFlag
        v-if="task.is_milestone"
        class="mt-0.5 size-3.5 shrink-0 text-ink-amber-3"
      />
      <p class="flex-1 text-sm leading-snug text-ink-gray-8">{{ task.subject }}</p>
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

    <!-- one quiet meta line instead of a wall of badges -->
    <div class="mt-2.5 flex items-center gap-2">
      <Tooltip :text="`Type: ${task.type || 'none'}`">
        <span
          class="shrink-0 text-[11px] font-medium uppercase tracking-wide"
          :class="typeStyle.text"
        >
          {{ typeStyle.short }}
        </span>
      </Tooltip>

      <PriorityIcon :priority="task.priority" />

      <Tooltip
        v-if="task.status === 'Pending Review' && task.review_date"
        :text="`Review by ${formatDate(task.review_date)}`"
      >
        <span
          class="inline-flex shrink-0 items-center gap-0.5 text-xs"
          :class="reviewLate ? 'font-medium text-ink-red-3' : 'text-ink-amber-3'"
        >
          <LucideClipboardCheck class="size-3" />
          {{ dueLabel(task.review_date) }}
        </span>
      </Tooltip>

      <Tooltip v-if="task.is_blocked" :text="blockedLabel">
        <LucideLock class="size-3.5 shrink-0 text-ink-amber-3" />
      </Tooltip>

      <span
        v-if="task.exp_end_date"
        class="shrink-0 text-xs"
        :class="overdue ? 'font-medium text-ink-red-3' : 'text-ink-gray-5'"
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
        class="shrink-0 rounded bg-surface-gray-2 px-1 text-[11px] tabular-nums text-ink-gray-6"
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
        class="h-full rounded-full bg-surface-blue-3"
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
import { taskTypeStyle } from '@/utils/constants'
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
