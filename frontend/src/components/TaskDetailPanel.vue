<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-150"
      leave-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="taskName"
        class="fixed inset-0 z-40 bg-black/20"
        @click="close"
      />
    </Transition>

    <Transition
      enter-active-class="transition-transform duration-200 ease-out"
      leave-active-class="transition-transform duration-150 ease-in"
      enter-from-class="translate-x-full"
      leave-to-class="translate-x-full"
    >
      <aside
        v-if="taskName"
        class="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-outline-gray-2 bg-surface-white pb-safe-bottom pt-safe-top shadow-lg sm:max-w-xl sm:border-l"
      >
        <!-- header -->
        <header
          class="flex shrink-0 items-center gap-2 border-b border-outline-gray-2 px-3 py-2.5 sm:px-4"
        >
          <button
            class="tap-target -ml-1 grid place-items-center rounded p-1 text-ink-gray-7 hover:bg-surface-gray-2 sm:hidden"
            aria-label="Close"
            @click="close"
          >
            <LucideArrowLeft class="size-5" />
          </button>
          <span class="font-mono text-xs text-ink-gray-5">{{ taskName }}</span>
          <Badge
            v-if="task?.project_title"
            theme="gray"
            variant="subtle"
            size="sm"
            class="hidden min-w-0 sm:inline-flex"
          >
            {{ task.project_title }}
          </Badge>
          <div class="ml-auto flex items-center gap-1">
            <TaskTimer
              v-if="permissions.canSubmitTimesheet && task"
              :task="task"
              @logged="reload"
            />
            <Dropdown :options="menuOptions" placement="bottom-end">
              <Button variant="ghost" size="sm">
                <LucideMoreHorizontal class="size-4" />
              </Button>
            </Dropdown>
            <Button variant="ghost" size="sm" class="hidden sm:inline-flex" @click="close">
              <LucideX class="size-4" />
            </Button>
          </div>
        </header>

        <div v-if="loading" class="flex flex-1 items-center justify-center">
          <LoadingIndicator class="size-5 text-ink-gray-5" />
        </div>
        <ErrorState v-else-if="loadError" :error="loadError" />

        <div v-else-if="task" class="thin-scrollbar min-h-0 flex-1 overflow-y-auto">
          <div class="flex flex-col gap-5 px-3 py-4 sm:px-4">
            <!-- subject -->
            <button
              v-if="task.epic"
              class="flex w-fit items-center gap-1.5 px-1.5 text-xs font-medium text-ink-gray-6 hover:text-ink-gray-8"
              @click="open(task.epic.name)"
            >
              <span
                class="size-2 shrink-0 rounded-[3px]"
                :style="{ backgroundColor: task.epic.color || '#9ca3af' }"
              />
              {{ task.epic.subject }}
            </button>

            <textarea
              ref="subjectBox"
              v-model="draftSubject"
              rows="1"
              class="w-full resize-none rounded border border-transparent bg-transparent px-1.5 py-1 text-lg font-semibold leading-snug text-ink-gray-9 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none"
              :readonly="!task.can_write"
              @input="autoGrow"
              @blur="saveSubject"
              @keydown.enter.prevent="$event.target.blur()"
            />

            <!-- properties -->
            <dl
              class="grid grid-cols-[6rem_minmax(0,1fr)] items-center gap-x-3 gap-y-2.5 sm:grid-cols-[7rem_minmax(0,1fr)]"
            >
              <dt class="text-xs text-ink-gray-5">Status</dt>
              <dd>
                <StatusPill
                  :status="task.status"
                  :editable="task.can_write"
                  @change="(v) => save({ status: v })"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Assignees</dt>
              <dd>
                <AssigneeSelect
                  :model-value="assigneeEmails"
                  @update:model-value="(v) => save({ assignees: v })"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Priority</dt>
              <dd>
                <PriorityIcon
                  :priority="task.priority"
                  :editable="task.can_write"
                  show-label
                  @change="(v) => save({ priority: v })"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Labels</dt>
              <dd>
                <TagInput
                  :model-value="task.tags || []"
                  :readonly="!task.can_write"
                  @update:model-value="saveTags"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Type</dt>
              <dd>
                <NullableSelect
                  :model-value="task.type || ''"
                  :options="typeOptions"
                  variant="ghost"
                  :disabled="!task.can_write"
                  @update:model-value="(v) => save({ type: v })"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Start date</dt>
              <dd>
                <DatePicker
                  :value="dateOnly(task.exp_start_date)"
                  placeholder="Not set"
                  variant="subtle"
                  :readonly="!task.can_write"
                  @update:model-value="(v) => save({ exp_start_date: v })"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Due date</dt>
              <dd class="flex items-center gap-2">
                <DatePicker
                  :value="dateOnly(task.exp_end_date)"
                  placeholder="Not set"
                  variant="subtle"
                  :readonly="!task.can_write"
                  @update:model-value="(v) => save({ exp_end_date: v })"
                />
                <Badge v-if="overdue" theme="red" variant="subtle" size="sm">
                  Overdue
                </Badge>
              </dd>

              <dt class="text-xs text-ink-gray-5">Weight</dt>
              <dd>
                <input
                  v-model.number="draftWeight"
                  type="number"
                  step="0.5"
                  min="0"
                  :readonly="!task.can_write"
                  class="h-7 w-20 rounded border border-transparent bg-transparent px-1.5 text-sm text-ink-gray-8 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none"
                  @blur="saveWeight"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Progress</dt>
              <dd>
                <Tooltip
                  :text="
                    progressLocked
                      ? 'ERPNext pins a completed task at 100%'
                      : 'Drag to set % progress'
                  "
                >
                  <ProgressSlider
                    v-model="draftProgress"
                    :disabled="!task.can_write || progressLocked"
                    @commit="(value) => save({ progress: value })"
                  />
                </Tooltip>
              </dd>

              <dt class="text-xs text-ink-gray-5">Time</dt>
              <dd class="text-sm text-ink-gray-7">
                {{ formatNumber(task.actual_time) }} h logged
                <span class="text-ink-gray-5">
                  / {{ formatNumber(task.expected_time) }} h estimated
                </span>
              </dd>
            </dl>

            <!-- description -->
            <section>
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Description
              </h3>
              <TextEditor
                :key="`desc-${task.name}`"
                editor-class="prose-f min-h-20 rounded border border-outline-gray-2 px-2.5 py-2 focus:outline-none"
                :content="task.description || ''"
                :editable="task.can_write"
                placeholder="Add a description…"
                @blur="saveDescription"
                @change="(value) => (draftDescription = value)"
              />
            </section>

            <!-- child issues -->
            <section v-if="task.subtasks?.length || task.is_group">
              <div class="mb-1.5 flex items-center gap-2">
                <h3 class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                  Child issues
                </h3>
                <span
                  v-if="task.subtask_progress?.total"
                  class="text-xs tabular-nums text-ink-gray-4"
                >
                  {{ task.subtask_progress.done }} of {{ task.subtask_progress.total }} done
                </span>
                <span
                  v-if="task.subtask_progress?.total"
                  class="h-1 w-20 overflow-hidden rounded-full bg-surface-gray-2"
                >
                  <span
                    class="block h-full rounded-full bg-surface-green-3"
                    :style="{ width: `${subtaskPercent}%` }"
                  />
                </span>
                <span class="ml-auto" />
                <Button
                  v-if="task.is_group && permissions.canCreateTask"
                  variant="ghost"
                  size="sm"
                  @click="showSubtask = true"
                >
                  <template #prefix><LucidePlus class="size-3.5" /></template>
                  Add
                </Button>
              </div>
              <ul class="flex flex-col divide-y divide-outline-gray-1">
                <li
                  v-for="sub in task.subtasks"
                  :key="sub.name"
                  class="flex cursor-pointer items-center gap-2 py-1.5 hover:bg-surface-gray-1"
                  @click="open(sub.name)"
                >
                  <span class="size-1.5 rounded-full" :class="statusStyle(sub.status).dot" />
                  <span class="flex-1 truncate text-sm text-ink-gray-8">
                    {{ sub.subject }}
                  </span>
                  <AvatarStack :users="sub.assignees || []" :max="2" size="xs" />
                </li>
                <li v-if="!task.subtasks?.length" class="py-2 text-xs text-ink-gray-4">
                  Nothing under this epic yet.
                </li>
              </ul>
            </section>

            <!-- dependencies (native Task Depends On) -->
            <section>
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Blocked by
              </h3>
              <DependencyPicker
                :dependencies="task.depends_on || []"
                :task="task.name"
                :project="task.project"
                :readonly="!task.can_write"
                @change="saveDependencies"
                @open="open"
              />
            </section>

            <section v-if="task.blocks?.length">
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Blocks
              </h3>
              <ul class="flex flex-col divide-y divide-outline-gray-1">
                <li
                  v-for="dep in task.blocks"
                  :key="dep.name"
                  class="flex cursor-pointer items-center gap-2 py-1.5 hover:bg-surface-gray-1"
                  @click="open(dep.name)"
                >
                  <span class="size-1.5 rounded-full" :class="statusStyle(dep.status).dot" />
                  <span class="flex-1 truncate text-sm text-ink-gray-8">{{ dep.subject }}</span>
                </li>
              </ul>
            </section>

            <!-- attachments -->
            <section>
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Attachments
              </h3>
              <TaskAttachments
                :files="task.attachments || []"
                :task="task.name"
                :readonly="!task.can_write"
                @change="(files) => (task.attachments = files)"
              />
            </section>

            <!-- time logs -->
            <section v-if="task.time_logs?.length">
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Time logs
              </h3>
              <ul class="flex flex-col divide-y divide-outline-gray-1 text-sm">
                <li
                  v-for="log in task.time_logs"
                  :key="log.name"
                  class="flex items-center gap-2 py-1.5"
                >
                  <span class="tabular-nums text-ink-gray-8">
                    {{ formatNumber(log.hours) }} h
                  </span>
                  <span class="truncate text-ink-gray-6">
                    {{ log.description || log.activity_type || '—' }}
                  </span>
                  <span class="ml-auto shrink-0 text-xs text-ink-gray-5">
                    {{ log.logged_by }} · {{ formatDate(log.from_time) }}
                  </span>
                </li>
              </ul>
            </section>

            <!-- change log, read from the Version records Frappe writes -->
            <section v-if="task.history?.length">
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                History
              </h3>
              <ul class="flex flex-col gap-2">
                <li
                  v-for="entry in task.history"
                  :key="entry.name"
                  class="flex gap-2 text-xs"
                >
                  <UserAvatar
                    :user="{ full_name: entry.full_name, user_image: entry.user_image }"
                    size="sm"
                  />
                  <p class="min-w-0 flex-1 text-ink-gray-6">
                    <span class="font-medium text-ink-gray-8">{{ entry.full_name }}</span>
                    <span v-for="(change, i) in entry.changes" :key="i">
                      changed {{ change.field }} from
                      <span class="text-ink-gray-8">{{ change.from || '—' }}</span>
                      to
                      <span class="text-ink-gray-8">{{ change.to || '—' }}</span>
                      <span v-if="i < entry.changes.length - 1">, </span>
                    </span>
                    <span class="text-ink-gray-4"> · {{ timeAgo(entry.creation) }}</span>
                  </p>
                </li>
              </ul>
            </section>

            <!-- comments -->
            <section>
              <h3 class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Comments
              </h3>
              <ul class="mb-3 flex flex-col gap-3">
                <li v-for="comment in task.comments" :key="comment.name" class="flex gap-2">
                  <UserAvatar
                    :user="{ full_name: comment.full_name, user_image: comment.user_image }"
                    size="sm"
                  />
                  <div class="min-w-0 flex-1">
                    <div class="flex items-baseline gap-2">
                      <span class="text-sm font-medium text-ink-gray-8">
                        {{ comment.full_name }}
                      </span>
                      <span class="text-xs text-ink-gray-5">
                        {{ timeAgo(comment.creation) }}
                      </span>
                      <button
                        v-if="comment.owner === currentUser"
                        class="ml-auto text-xs text-ink-gray-5 hover:text-ink-red-3"
                        @click="removeComment(comment)"
                      >
                        Delete
                      </button>
                    </div>
                    <div class="prose-f mt-0.5 text-sm" v-html="comment.content" />
                  </div>
                </li>
                <li v-if="!task.comments?.length" class="text-xs text-ink-gray-5">
                  No comments yet.
                </li>
              </ul>

              <div class="flex gap-2">
                <UserAvatar :user="user" size="sm" />
                <div class="flex-1">
                  <TextEditor
                    ref="commentEditor"
                    :key="`comment-${task.name}-${commentKey}`"
                    editor-class="prose-f min-h-14 rounded border border-outline-gray-2 px-2.5 py-2 focus:outline-none"
                    content=""
                    placeholder="Leave a comment…"
                    @change="(value) => (newComment = value)"
                  />
                  <div class="mt-2 flex justify-end">
                    <Button
                      variant="solid"
                      size="sm"
                      :loading="postingComment"
                      :disabled="!hasCommentText"
                      @click="postComment"
                    >
                      Comment
                    </Button>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        <LogTimeDialog v-model="showLogTime" :task="task" @logged="reload" />
        <CreateTaskDialog
          v-model="showSubtask"
          :project="task?.project"
          :default-parent="task?.name"
          @created="onSubtaskCreated"
        />
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Badge,
  Button,
  DatePicker,
  Dropdown,
  LoadingIndicator,
  TextEditor,
  toast,
} from 'frappe-ui'
import AssigneeSelect from './AssigneeSelect.vue'
import AvatarStack from './AvatarStack.vue'
import CreateTaskDialog from './CreateTaskDialog.vue'
import DependencyPicker from './DependencyPicker.vue'
import ErrorState from './ErrorState.vue'
import LogTimeDialog from './LogTimeDialog.vue'
import NullableSelect from './NullableSelect.vue'
import TagInput from './TagInput.vue'
import TaskAttachments from './TaskAttachments.vue'
import TaskTimer from './TaskTimer.vue'
import PriorityIcon from './PriorityIcon.vue'
import ProgressSlider from './ProgressSlider.vue'
import StatusPill from './StatusPill.vue'
import UserAvatar from './UserAvatar.vue'
import api from '@/data/api'
import { removeTask, upsertTask } from '@/data/board'
import { permissions, taskTypes, user } from '@/data/session'
import { isNarrow } from '@/data/ui'
import { statusStyle } from '@/utils/constants'
import { formatDate, formatNumber, isOverdue, plainText, timeAgo } from '@/utils/format'
import { closeTask, openTask } from '@/utils/taskPanel'

const route = useRoute()

const task = ref(null)
const loading = ref(false)
const loadError = ref(null)
const showLogTime = ref(false)
const showSubtask = ref(false)

const subjectBox = ref(null)
const draftSubject = ref('')
const draftDescription = ref('')
const draftWeight = ref(0)
const draftProgress = ref(0)
const newComment = ref('')
const commentKey = ref(0)
const postingComment = ref(false)

const taskName = computed(() => route.query.task || null)
const currentUser = computed(() => user.value?.name)
const assigneeEmails = computed(() => (task.value?.assignees || []).map((u) => u.name))
/** ERPNext forces progress to 100 on a completed task, so do not fight it. */
const progressLocked = computed(() => task.value?.status === 'Completed')

const subtaskPercent = computed(() => {
  const p = task.value?.subtask_progress
  return p?.total ? Math.round((p.done / p.total) * 100) : 0
})

const overdue = computed(() =>
  task.value ? isOverdue(task.value.exp_end_date, task.value.status) : false,
)
const hasCommentText = computed(() => Boolean(plainText(newComment.value).trim()))

const typeOptions = computed(() => [
  { label: 'No type', value: '' },
  ...taskTypes.value.map((t) => ({ label: t, value: t })),
])

const menuOptions = computed(() => [
  ...(permissions.value.canSubmitTimesheet
    ? [
        {
          label: 'Log time manually…',
          icon: 'clock',
          onClick: () => (showLogTime.value = true),
        },
      ]
    : []),
  {
    label: 'Open in Desk',
    icon: 'external-link',
    onClick: () => window.open(`/app/task/${task.value.name}`, '_blank'),
  },
  {
    label: 'Copy link',
    icon: 'link',
    onClick: () => {
      navigator.clipboard?.writeText(window.location.href)
      toast.success('Link copied')
    },
  },
  ...(task.value?.can_delete
    ? [{ label: 'Delete task', icon: 'trash-2', onClick: destroy }]
    : []),
])

function close() {
  closeTask()
}

function open(name) {
  openTask(name)
}

function dateOnly(value) {
  return value ? String(value).slice(0, 10) : ''
}

function syncDrafts() {
  draftSubject.value = task.value?.subject || ''
  draftDescription.value = task.value?.description || ''
  draftWeight.value = task.value?.task_weight || 0
  draftProgress.value = Math.round(task.value?.progress || 0)
  // The subject box only auto-grows on input, so size it for the loaded value
  // too - otherwise a subject that wraps gets clipped to one line.
  nextTick(resizeSubject)
}

function resizeSubject() {
  const el = subjectBox.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

async function load(name) {
  loading.value = true
  loadError.value = null
  try {
    task.value = await api.getTask(name)
    syncDrafts()
  } catch (e) {
    loadError.value = e
    task.value = null
  } finally {
    loading.value = false
  }
}

async function reload() {
  if (taskName.value) await load(taskName.value)
}

async function save(values) {
  if (!task.value?.can_write) return
  try {
    const updated = await api.updateTask(task.value.name, values)
    task.value = updated
    syncDrafts()
    upsertTask(updated)
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Update failed')
    await reload()
  }
}

function saveSubject() {
  const value = draftSubject.value.trim()
  if (!value || value === task.value.subject) {
    draftSubject.value = task.value.subject
    return
  }
  save({ subject: value })
}

async function saveTags(tags) {
  if (!task.value?.can_write) return
  const previous = task.value.tags || []
  task.value.tags = tags
  try {
    const saved = await api.setTaskTags(task.value.name, tags)
    task.value.tags = saved
    upsertTask({ name: task.value.name, tags: saved })
  } catch (e) {
    task.value.tags = previous
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update labels')
  }
}

async function saveDependencies(names) {
  if (!task.value?.can_write) return
  try {
    await api.setDependencies(task.value.name, names)
    await reload()
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update dependencies')
  }
}

function saveWeight() {
  const value = Number(draftWeight.value) || 0
  if (value === (task.value.task_weight || 0)) return
  save({ task_weight: value })
}

function saveDescription() {
  if (draftDescription.value === (task.value.description || '')) return
  save({ description: draftDescription.value })
}

function autoGrow(event) {
  event.target.style.height = 'auto'
  event.target.style.height = `${event.target.scrollHeight}px`
}

// A viewport change rewraps the subject, so re-measure.
watch(isNarrow, () => nextTick(resizeSubject))

async function postComment() {
  if (!hasCommentText.value) return
  postingComment.value = true
  try {
    const comment = await api.addComment('Task', task.value.name, newComment.value)
    task.value.comments = [...(task.value.comments || []), comment]
    newComment.value = ''
    commentKey.value += 1
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not post comment')
  } finally {
    postingComment.value = false
  }
}

async function removeComment(comment) {
  try {
    await api.deleteComment(comment.name)
    task.value.comments = task.value.comments.filter((c) => c.name !== comment.name)
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not delete comment')
  }
}

async function destroy() {
  if (!window.confirm(`Delete ${task.value.name}? This cannot be undone.`)) return
  try {
    await api.deleteTask(task.value.name)
    removeTask(task.value.name)
    toast.success('Task deleted')
    close()
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not delete the task')
  }
}

function onSubtaskCreated(created) {
  upsertTask(created)
  reload()
}

watch(
  taskName,
  async (name) => {
    if (!name) {
      task.value = null
      return
    }
    await load(name)
    await nextTick()
  },
  { immediate: true },
)

// Esc closes the panel, like every other issue tracker.
function onKeydown(event) {
  if (event.key === 'Escape' && taskName.value && !showLogTime.value && !showSubtask.value) {
    close()
  }
}
window.addEventListener('keydown', onKeydown)
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>
