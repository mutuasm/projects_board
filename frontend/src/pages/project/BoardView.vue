<template>
  <div class="flex h-full min-h-0">
    <EpicRail
      v-if="!isNarrow"
      v-model="filters.epic"
      class="hidden lg:flex"
      :epics="epics"
      :total-tasks="tasks.length"
      :collapsed="railCollapsed"
      :can-create="permissions.canCreateTask"
      @toggle="toggleRail"
      @create="createEpic"
    />

    <div class="min-w-0 flex-1">
      <BoardSkeleton v-if="loading" />

      <div v-else class="no-scrollbar snap-columns h-full overflow-auto">
        <div class="min-w-max p-3 pb-24 sm:p-4 sm:pb-6" :class="single ? 'h-full' : ''">
          <section
            v-for="lane in pagedLanes"
            :key="lane.key"
            :data-lane="lane.key"
            class="mb-5 last:mb-0"
            :class="single ? 'h-full' : ''"
          >
            <!-- swimlane header -->
            <header v-if="!single" class="sticky left-0 mb-2 flex w-fit items-center gap-2">
              <button
                class="flex items-center gap-2 rounded-4 px-1.5 py-1 hover:bg-surface-gray-2"
                @click="toggleLane(lane.key)"
              >
                <LucideChevronRight
                  class="size-3.5 text-ink-gray-5 transition-transform"
                  :class="collapsedLanes.has(lane.key) ? '' : 'rotate-90'"
                />
                <span
                  v-if="lane.color"
                  class="size-2 shrink-0 rounded-[3px]"
                  :style="{ backgroundColor: lane.color }"
                />
                <UserAvatar v-if="lane.user" :user="lane.user" size="sm" />
                <span class="text-sm-medium text-ink-gray-8">{{ lane.label }}</span>
                <span class="text-xs tabular-nums text-ink-gray-4">{{ lane.count }}</span>
              </button>
            </header>

            <div
              v-show="single || !collapsedLanes.has(lane.key)"
              class="flex gap-3"
              :class="single ? 'h-full items-stretch' : 'items-start'"
            >
              <section
                v-for="status in columns"
                :key="status"
                class="flex w-[82vw] max-w-xs shrink-0 flex-col sm:w-72 sm:max-w-none"
                :class="single ? 'h-full' : 'max-h-[70vh]'"
              >
                <!-- flat column head: a rule, not a filled box -->
                <header
                  class="flex items-center gap-2 border-b border-outline-gray-2 px-1 pb-2"
                >
                  <span class="size-1.5 rounded-full" :class="statusStyle(status).dot" />
                  <h2 class="text-xs-medium uppercase tracking-wide text-ink-gray-6">
                    {{ statusStyle(status).label || status }}
                  </h2>
                  <span class="text-xs tabular-nums text-ink-gray-4">
                    {{ lane.totals[status] || 0 }}
                  </span>
                  <button
                    v-if="permissions.canCreateTask && status !== 'Cancelled'"
                    class="tap-target ml-auto grid place-items-center rounded-4 p-1 text-ink-gray-4 hover:bg-surface-gray-2 hover:text-ink-gray-7"
                    :aria-label="`Add task to ${status}`"
                    @click="quickAdd(status)"
                  >
                    <LucidePlus class="size-3.5" />
                  </button>
                </header>

                <draggable
                  :list="lane.columns[status]"
                  :group="{ name: 'tasks' }"
                  item-key="name"
                  class="thin-scrollbar flex min-h-16 flex-1 flex-col gap-2 overflow-y-auto rounded-b-5 px-1 pb-3 pt-2 transition-colors"
                  ghost-class="task-ghost"
                  drag-class="task-drag"
                  :animation="150"
                  :delay="isTouch ? 180 : 0"
                  :delay-on-touch-only="true"
                  :touch-start-threshold="6"
                  :scroll-sensitivity="80"
                  :force-fallback="isTouch"
                  @change="(event) => onChange(status, event)"
                >
                  <template #item="{ element }">
                    <TaskCard :task="element" @filter-epic="(e) => (filters.epic = e)" />
                  </template>
                  <template #footer>
                    <LoadMore
                      v-if="(lane.totals[status] || 0) > limitFor(lane.key, status)"
                      @more="moreFor(lane.key, status)"
                    />
                    <div
                      v-if="!(lane.columns[status] || []).length"
                      class="rounded-5 border border-dashed border-outline-gray-2 py-6 text-center text-xs text-ink-gray-4"
                    >
                      Drop tasks here
                    </div>
                  </template>
                </draggable>
              </section>
            </div>
          </section>
        </div>
      </div>
    </div>

    <CreateTaskDialog
      v-model="showQuickAdd"
      :project="project"
      :default-status="quickAddStatus"
      :default-is-group="creatingEpic"
      :default-parent="creatingEpic ? null : selectedEpicParent"
      @created="onCreated"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, watchEffect } from 'vue'
import draggable from 'vuedraggable'
import { toast } from 'frappe-ui'
import BoardSkeleton from '@/components/BoardSkeleton.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import LoadMore from '@/components/LoadMore.vue'
import EpicRail from '@/components/EpicRail.vue'
import TaskCard from '@/components/TaskCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import api from '@/data/api'
import {
  buildLanes,
  epics,
  filters,
  loadEpics,
  loading,
  reloadTasks,
  selectedEpicParent,
  tasks,
  upsertTask,
} from '@/data/board'
import { EVENTS, on } from '@/data/bus'
import { boardStatuses, permissions } from '@/data/session'
import { isNarrow, isTouch } from '@/data/ui'
import { statusStyle } from '@/utils/constants'

const props = defineProps({ project: { type: String, required: true } })

const showQuickAdd = ref(false)
const quickAddStatus = ref('Open')
const creatingEpic = ref(false)
const collapsedLanes = ref(new Set())
const railCollapsed = ref(localStorage.getItem('pb:epic-rail') === '0')

const columns = computed(() => boardStatuses.value)
/** Without swimlanes the board is one full-height row of columns. */
const single = computed(() => filters.swimlane === 'none')

/**
 * Sortable mutates the array it is bound to, so the lanes live in a ref that is
 * recomputed whenever the store changes. A dropped card then stays put while
 * the server round-trip is in flight instead of snapping back for a frame.
 */
const lanes = ref([])
watchEffect(() => {
  lanes.value = buildLanes(columns.value, filters.swimlane)
})

/**
 * A column renders 30 cards and grows as you scroll down it, so a project with
 * hundreds of tasks still opens instantly. Sortable gets the page-sized slice;
 * the counts in the column heads stay the full totals.
 */
const COLUMN_PAGE = 30
const columnLimits = ref({})
const limitFor = (lane, status) => columnLimits.value[`${lane}|${status}`] || COLUMN_PAGE
function moreFor(lane, status) {
  columnLimits.value = {
    ...columnLimits.value,
    [`${lane}|${status}`]: limitFor(lane, status) + COLUMN_PAGE,
  }
}
watch(
  () => [props.project, filters.swimlane],
  () => (columnLimits.value = {}),
)

const pagedLanes = computed(() =>
  lanes.value.map((lane) => {
    const columns = {}
    const totals = {}
    for (const [status, list] of Object.entries(lane.columns)) {
      columns[status] = list.slice(0, limitFor(lane.key, status))
      totals[status] = list.length
    }
    return { ...lane, columns, totals }
  }),
)

function toggleRail() {
  railCollapsed.value = !railCollapsed.value
  localStorage.setItem('pb:epic-rail', railCollapsed.value ? '0' : '1')
}

function toggleLane(key) {
  const next = new Set(collapsedLanes.value)
  next.has(key) ? next.delete(key) : next.add(key)
  collapsedLanes.value = next
}

function quickAdd(status) {
  quickAddStatus.value = status
  creatingEpic.value = false
  showQuickAdd.value = true
}

function createEpic() {
  quickAddStatus.value = 'Open'
  creatingEpic.value = true
  showQuickAdd.value = true
}

async function onCreated(task) {
  upsertTask(task)
  // a new epic has to appear in the rail straight away
  if (task.is_group) await loadEpics(props.project)
}

/**
 * vuedraggable fires `added` on the destination column. Moving across a
 * swimlane boundary would also change the lane's dimension (assignee, say),
 * which we deliberately do not do - only the status follows the drop.
 */
async function onChange(status, event) {
  const moved = event?.added?.element
  if (!moved || moved.status === status) return

  const previous = moved.status
  moved.status = status // optimistic

  try {
    const updated = await api.moveTask(moved.name, status)
    upsertTask(updated)
    if (updated.parent_task || updated.is_group) await loadEpics(props.project)
  } catch (e) {
    moved.status = previous
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not move this task')
    await reloadTasks()
  }
}

let off = null
onMounted(() => {
  off = on(EVENTS.CREATE_TASK, () => quickAdd('Open'))
})
onUnmounted(() => off?.())
</script>
