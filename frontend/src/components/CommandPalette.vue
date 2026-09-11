<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="flex flex-col">
        <div class="flex items-center gap-2 border-b border-outline-gray-2 px-4 py-3">
          <LucideSearch class="size-4 shrink-0 text-ink-gray-4" />
          <input
            ref="input"
            v-model="query"
            type="text"
            placeholder="Search tasks and projects, or jump to a view…"
            class="w-full border-none bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="run(flat[cursor])"
            @keydown.esc="show = false"
          />
          <LoadingIndicator v-if="searching" class="size-4 text-ink-gray-5" />
          <kbd
            class="hidden rounded border border-outline-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-5 sm:block"
          >
            esc
          </kbd>
        </div>

        <div class="thin-scrollbar max-h-96 overflow-y-auto p-1.5">
          <template v-for="group in groups" :key="group.label">
            <p
              v-if="group.items.length"
              class="px-2.5 pb-1 pt-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5"
            >
              {{ group.label }}
            </p>
            <button
              v-for="item in group.items"
              :key="item.key"
              class="flex w-full items-center gap-2.5 rounded px-2.5 py-2 text-left"
              :class="
                flat[cursor]?.key === item.key ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-2'
              "
              @click="run(item)"
              @mousemove="cursor = flat.findIndex((i) => i.key === item.key)"
            >
              <component :is="item.icon" class="size-4 shrink-0 text-ink-gray-5" />
              <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">
                {{ item.label }}
              </span>
              <span v-if="item.hint" class="shrink-0 text-xs text-ink-gray-5">
                {{ item.hint }}
              </span>
            </button>
          </template>

          <p v-if="!flat.length" class="px-2.5 py-6 text-center text-sm text-ink-gray-5">
            Nothing matches “{{ query }}”
          </p>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Dialog, LoadingIndicator } from 'frappe-ui'
import api from '@/data/api'
import { projects } from '@/data/projects'
import { openTask } from '@/utils/taskPanel'
import { debounce } from '@/utils/debounce'

import LucideLayoutGrid from '~icons/lucide/layout-grid'
import LucideCircleUser from '~icons/lucide/circle-user'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucideFolder from '~icons/lucide/folder'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const router = useRouter()
const input = ref(null)
const query = ref('')
const cursor = ref(0)
const taskResults = ref([])
const searching = ref(false)

const navItems = computed(() =>
  [
    {
      key: 'nav:my-work',
      label: 'My Work',
      icon: LucideCircleUser,
      hint: 'g then w',
      run: () => router.push({ name: 'MyWork' }),
    },
    {
      key: 'nav:projects',
      label: 'All projects',
      icon: LucideLayoutGrid,
      hint: 'g then p',
      run: () => router.push({ name: 'Projects' }),
    },
  ].filter((item) => matches(item.label)),
)

const projectItems = computed(() =>
  projects.value
    .filter((p) => matches(p.project_name))
    .slice(0, 6)
    .map((p) => ({
      key: `project:${p.name}`,
      label: p.project_name,
      icon: LucideFolder,
      hint: `${p.open_tasks} open`,
      run: () => router.push({ name: 'Board', params: { project: p.name } }),
    })),
)

const taskItems = computed(() =>
  taskResults.value.map((t) => ({
    key: `task:${t.name}`,
    label: t.subject,
    icon: LucideSquareCheck,
    hint: t.status,
    run: () => openTask(t.name),
  })),
)

const groups = computed(() => [
  { label: 'Go to', items: navItems.value },
  { label: 'Projects', items: projectItems.value },
  { label: 'Tasks', items: taskItems.value },
])

const flat = computed(() => groups.value.flatMap((g) => g.items))

function matches(text) {
  const q = query.value.trim().toLowerCase()
  return !q || String(text).toLowerCase().includes(q)
}

const searchTasks = debounce(async (txt) => {
  if (!txt || txt.length < 2) {
    taskResults.value = []
    searching.value = false
    return
  }
  searching.value = true
  try {
    taskResults.value = (await api.searchTasks({ txt, limit: 8 })) || []
  } finally {
    searching.value = false
  }
}, 250)

watch(query, (value) => {
  cursor.value = 0
  searchTasks(value.trim())
})

watch(show, async (open) => {
  if (!open) return
  query.value = ''
  taskResults.value = []
  cursor.value = 0
  await nextTick()
  input.value?.focus()
})

function move(delta) {
  if (!flat.value.length) return
  cursor.value = (cursor.value + delta + flat.value.length) % flat.value.length
}

function run(item) {
  if (!item) return
  show.value = false
  item.run()
}
</script>
