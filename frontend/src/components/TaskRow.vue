<template>
  <div
    class="group relative flex cursor-pointer flex-col gap-2 border-b border-outline-gray-1 py-2.5 pr-2 md:grid md:grid-cols-[1.5rem_minmax(0,1fr)_7rem_7rem_6rem_6rem_5rem] md:items-center md:gap-3 md:py-1.5"
    :class="selection.has(task.name) ? 'bg-surface-gray-2' : 'hover:bg-surface-gray-1'"
    :style="{ paddingLeft: `${0.5 + depth * 1.25}rem` }"
    @click="openTask(task.name)"
  >
    <!-- tree guide: a hairline for every level above this row -->
    <span
      v-for="level in depth"
      :key="level"
      class="pointer-events-none absolute top-0 h-full w-px bg-outline-gray-2"
      :style="{ left: `${0.95 + (level - 1) * 1.25}rem` }"
      aria-hidden="true"
    />

    <input
      type="checkbox"
      class="relative hidden size-3.5 rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0 md:block"
      :checked="selection.has(task.name)"
      :aria-label="`Select ${task.subject}`"
      @click.stop
      @change="toggleSelected(task.name)"
    />

    <div class="flex min-w-0 items-start gap-1.5 md:items-center">
      <!-- expander, or a spacer so leaf rows still line up -->
      <button
        v-if="hasChildren"
        class="grid size-4 shrink-0 place-items-center rounded text-ink-gray-5 hover:bg-surface-gray-3"
        :aria-label="expanded ? 'Collapse' : 'Expand'"
        @click.stop="$emit('toggle')"
      >
        <LucideChevronRight
          class="size-3.5 transition-transform"
          :class="expanded ? 'rotate-90' : ''"
        />
      </button>
      <span v-else class="size-4 shrink-0" />

      <span
        v-if="task.is_group"
        class="size-2 shrink-0 rounded-[3px]"
        :style="{ backgroundColor: task.color || '#9ca3af' }"
        title="Epic"
      />
      <LucideFlag
        v-else-if="task.is_milestone"
        class="size-3.5 shrink-0 text-ink-amber-3"
      />
      <span
        v-else
        class="shrink-0 text-[11px] font-medium uppercase tracking-wide"
        :class="typeStyle.text"
      >
        {{ typeStyle.short }}
      </span>

      <span
        class="min-w-0 flex-1 text-sm md:truncate"
        :class="task.is_group ? 'font-medium text-ink-gray-9' : 'text-ink-gray-8'"
      >
        {{ task.subject }}
      </span>

      <span
        v-if="hasChildren"
        class="shrink-0 rounded bg-surface-gray-2 px-1.5 text-[11px] tabular-nums text-ink-gray-6"
        :title="`${childCount} child issues`"
      >
        {{ childCount }}
      </span>
      <LucideLock
        v-if="task.is_blocked"
        class="size-3.5 shrink-0 text-ink-amber-3"
        title="Blocked"
      />
      <span
        v-if="task.tags?.length"
        class="hidden shrink-0 truncate text-[11px] text-ink-gray-5 lg:inline"
      >
        {{ task.tags.join(' · ') }}
      </span>
      <span class="hidden shrink-0 font-mono text-xs text-ink-gray-4 sm:inline">
        {{ task.name }}
      </span>
    </div>

    <div class="flex flex-wrap items-center gap-x-3 gap-y-2 md:contents">
      <div @click.stop>
        <StatusPill
          :status="task.status"
          editable
          @change="(s) => $emit('field', task, 'status', s)"
        />
      </div>

      <div @click.stop>
        <PriorityIcon
          :priority="task.priority"
          editable
          show-label
          @change="(p) => $emit('field', task, 'priority', p)"
        />
      </div>

      <span
        v-if="task.exp_end_date || !isNarrow"
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

      <span
        v-if="task.task_weight || !isNarrow"
        class="text-xs tabular-nums text-ink-gray-6 md:text-right"
        title="Weight"
      >
        {{ task.task_weight ? formatNumber(task.task_weight) : '—' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AvatarStack from './AvatarStack.vue'
import PriorityIcon from './PriorityIcon.vue'
import StatusPill from './StatusPill.vue'
import { selection, toggleSelected } from '@/data/board'
import { isNarrow } from '@/data/ui'
import { taskTypeStyle } from '@/utils/constants'
import { dueLabel, formatNumber, isOverdue } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

const props = defineProps({
  task: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  hasChildren: { type: Boolean, default: false },
  childCount: { type: Number, default: 0 },
  expanded: { type: Boolean, default: true },
})
defineEmits(['toggle', 'field'])

const typeStyle = computed(() => taskTypeStyle(props.task.type))
</script>
