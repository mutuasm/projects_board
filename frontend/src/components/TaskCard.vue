<template>
  <div
    class="group cursor-pointer rounded-lg border border-outline-gray-2 bg-surface-white p-2.5 shadow-sm transition-shadow hover:border-outline-gray-3 hover:shadow"
    @click="openTask(task.name)"
  >
    <!-- colour stripe uses the native Task.color field -->
    <div
      v-if="task.color"
      class="mb-2 h-1 w-8 rounded-full"
      :style="{ backgroundColor: task.color }"
    />

    <div class="flex items-start gap-2">
      <LucideFlag
        v-if="task.is_milestone"
        class="mt-0.5 size-3.5 shrink-0 text-ink-amber-3"
      />
      <p class="flex-1 text-sm leading-snug text-ink-gray-8">
        {{ task.subject }}
      </p>
    </div>

    <p
      v-if="preview"
      class="mt-1 line-clamp-2 text-xs leading-relaxed text-ink-gray-5"
    >
      {{ preview }}
    </p>

    <!-- meta chips -->
    <div class="mt-2.5 flex flex-wrap items-center gap-1.5">
      <Badge v-if="task.type" theme="gray" variant="subtle" size="sm">
        {{ task.type }}
      </Badge>
      <Badge
        v-if="task.task_weight"
        theme="gray"
        variant="subtle"
        size="sm"
        :title="'Weight (story points)'"
      >
        {{ formatNumber(task.task_weight) }}
      </Badge>
      <span
        v-if="task.exp_end_date"
        class="inline-flex items-center gap-1 rounded px-1 py-0.5 text-xs"
        :class="
          overdue
            ? 'bg-surface-red-2 text-ink-red-3'
            : 'text-ink-gray-5'
        "
      >
        <LucideCalendar class="size-3" />
        {{ dueLabel(task.exp_end_date) }}
      </span>
      <span
        v-if="task.comment_count"
        class="inline-flex items-center gap-0.5 text-xs text-ink-gray-5"
      >
        <LucideMessageSquare class="size-3" />
        {{ task.comment_count }}
      </span>
    </div>

    <div class="mt-2.5 flex items-center justify-between">
      <div class="flex items-center gap-1.5">
        <PriorityIcon :priority="task.priority" />
        <span class="font-mono text-xs text-ink-gray-4">{{ task.name }}</span>
      </div>
      <AvatarStack :users="task.assignees || []" :max="3" size="xs" />
    </div>

    <!-- progress on partially-done work -->
    <div
      v-if="task.progress > 0 && task.progress < 100"
      class="mt-2 h-1 w-full overflow-hidden rounded-full bg-surface-gray-2"
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
import { Badge } from 'frappe-ui'
import AvatarStack from './AvatarStack.vue'
import PriorityIcon from './PriorityIcon.vue'
import { dueLabel, formatNumber, isOverdue, plainText } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

const props = defineProps({
  task: { type: Object, required: true },
})

const preview = computed(() => plainText(props.task.description, 90))
const overdue = computed(() =>
  isOverdue(props.task.exp_end_date, props.task.status),
)
</script>
