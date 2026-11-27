<template>
  <aside
    class="flex h-full shrink-0 flex-col border-r border-outline-gray-2 transition-all"
    :class="collapsed ? 'w-10' : 'w-60'"
  >
    <header class="flex items-center gap-1 px-2 py-2.5">
      <button
        class="tap-target grid place-items-center rounded-4 p-1 text-ink-gray-5 hover:bg-surface-gray-2"
        :title="collapsed ? 'Show epics' : 'Hide epics'"
        @click="$emit('toggle')"
      >
        <LucideLayers class="size-4" />
      </button>
      <span
        v-if="!collapsed"
        class="text-xs-medium uppercase tracking-wide text-ink-gray-5"
      >
        Epics
      </span>
      <button
        v-if="!collapsed && canCreate"
        class="tap-target ml-auto grid place-items-center rounded-4 p-1 text-ink-gray-5 hover:bg-surface-gray-2"
        aria-label="New epic"
        @click="$emit('create')"
      >
        <LucidePlus class="size-3.5" />
      </button>
    </header>

    <div v-if="!collapsed" class="thin-scrollbar min-h-0 flex-1 overflow-y-auto px-2 pb-3">
      <button
        class="mb-0.5 flex w-full items-center gap-2 rounded-4 px-2 py-1.5 text-left text-sm transition-colors"
        :class="
          !modelValue
            ? 'bg-surface-gray-3 font-medium text-ink-gray-9'
            : 'text-ink-gray-7 hover:bg-surface-gray-2'
        "
        @click="$emit('update:modelValue', null)"
      >
        <LucideInbox class="size-3.5 shrink-0 text-ink-gray-5" />
        <span class="flex-1 truncate">All work</span>
        <span class="text-xs tabular-nums text-ink-gray-4">{{ totalTasks }}</span>
      </button>

      <button
        v-for="epic in epics"
        :key="epic.name"
        class="mb-0.5 flex w-full flex-col gap-1.5 rounded-4 px-2 py-1.5 text-left transition-colors"
        :class="
          modelValue === epic.name
            ? 'bg-surface-gray-3'
            : 'hover:bg-surface-gray-2'
        "
        @click="$emit('update:modelValue', modelValue === epic.name ? null : epic.name)"
      >
        <span class="flex items-center gap-2">
          <span
            class="size-2 shrink-0 rounded-[3px]"
            :style="{ backgroundColor: epic.color || '#9ca3af' }"
          />
          <span
            class="flex-1 truncate text-sm"
            :class="modelValue === epic.name ? 'font-medium text-ink-gray-9' : 'text-ink-gray-7'"
          >
            {{ epic.subject }}
          </span>
          <span class="shrink-0 text-xs tabular-nums text-ink-gray-4">
            {{ epic.done }}/{{ epic.total }}
          </span>
        </span>

        <!-- a hairline progress bar reads faster than another number -->
        <span class="h-0.5 w-full overflow-hidden rounded-full bg-surface-gray-3">
          <span
            class="block h-full rounded-full transition-all"
            :style="{
              width: `${epic.percent}%`,
              backgroundColor: epic.color || 'var(--surface-green-7)',
            }"
            :class="epic.color ? '' : 'bg-surface-green-7'"
          />
        </span>
      </button>

      <p v-if="!epics.length" class="px-2 py-3 text-xs leading-relaxed text-ink-gray-4">
        No epics yet. Create a task with “Epic” ticked to group work under it.
      </p>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  epics: { type: Array, default: () => [] },
  modelValue: { type: String, default: null },
  totalTasks: { type: Number, default: 0 },
  collapsed: { type: Boolean, default: false },
  canCreate: { type: Boolean, default: false },
})
defineEmits(['update:modelValue', 'toggle', 'create'])
</script>
