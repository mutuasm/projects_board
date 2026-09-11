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
        class="fixed inset-y-0 right-0 z-50 flex w-full max-w-xl flex-col border-l border-outline-gray-2 bg-surface-white shadow-2xl"
      >
        <!-- header -->
        <header
          class="flex shrink-0 items-center gap-2 border-b border-outline-gray-2 px-4 py-2.5"
        >
          <span class="font-mono text-xs text-ink-gray-5">{{ taskName }}</span>
          <Badge v-if="task?.project_title" theme="gray" variant="subtle" size="sm">
            {{ task.project_title }}
          </Badge>
          <div class="ml-auto flex items-center gap-1">
            <Button
              v-if="permissions.canSubmitTimesheet"
              variant="ghost"
              size="sm"
              @click="showLogTime = true"
            >
              <template #prefix><LucideTimer class="size-4" /></template>
              Log time
            </Button>
            <Dropdown :options="menuOptions" placement="bottom-end">
              <Button variant="ghost" size="sm">
                <LucideMoreHorizontal class="size-4" />
              </Button>
            </Dropdown>
            <Button variant="ghost" size="sm" @click="close">
              <LucideX class="size-4" />
            </Button>
          </div>
        </header>

        <div v-if="loading" class="flex flex-1 items-center justify-center">
          <LoadingIndicator class="size-5 text-ink-gray-5" />
        </div>
        <ErrorState v-else-if="loadError" :error="loadError" />

        <div v-else-if="task" class="thin-scrollbar min-h-0 flex-1 overflow-y-auto">
          <div class="flex flex-col gap-5 px-4 py-4">
            <!-- subject -->
            <textarea
              v-model="draftSubject"
              rows="1"
              class="w-full resize-none rounded border border-transparent bg-transparent px-1.5 py-1 text-lg font-semibold leading-snug text-ink-gray-9 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none"
              :readonly="!task.can_write"
              @input="autoGrow"
              @blur="saveSubject"
              @keydown.enter.prevent="$event.target.blur()"
            />

            <!-- properties -->
            <dl class="grid grid-cols-[7rem_minmax(0,1fr)] items-center gap-x-3 gap-y-2">
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

              <dt class="text-xs text-ink-gray-5">Type</dt>
              <dd>
                <Select
                  :model-value="task.type || ''"
                  :options="typeOptions"
                  size="sm"
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
                  variant="ghost"
                  :readonly="!task.can_write"
                  @update:model-value="(v) => save({ exp_start_date: v })"
                />
              </dd>

              <dt class="text-xs text-ink-gray-5">Due date</dt>
              <dd class="flex items-center gap-2">
                <DatePicker
                  :value="dateOnly(task.exp_end_date)"
                  placeholder="Not set"
                  variant="ghost"
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
              <dd class="flex items-center gap-2">
                <input
                  v-model.number="draftProgress"
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  :disabled="!task.can_write"
                  class="h-1 flex-1 accent-gray-800"
                  @change="save({ progress: draftProgress })"
                />
                <span class="w-10 text-right text-xs tabular-nums text-ink-gray-7">
                  {{ draftProgress }}%
                </span>
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

            <!-- subtasks -->
            <section v-if="task.subtasks?.length || task.is_group">
              <div class="mb-1.5 flex items-center justify-between">
                <h3 class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                  Subtasks
                </h3>
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
                <li v-if="!task.subtasks?.length" class="py-2 text-xs text-ink-gray-5">
                  No subtasks yet.
                </li>
              </ul>
            </section>

            <!-- dependencies -->
            <section v-if="task.depends_on?.length">
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Blocked by
              </h3>
              <ul class="flex flex-col divide-y divide-outline-gray-1">
                <li
                  v-for="dep in task.depends_on"
                  :key="dep.name"
                  class="flex cursor-pointer items-center gap-2 py-1.5 hover:bg-surface-gray-1"
                  @click="open(dep.name)"
                >
                  <span class="size-1.5 rounded-full" :class="statusStyle(dep.status).dot" />
                  <span class="flex-1 truncate text-sm text-ink-gray-8">
                    {{ dep.subject }}
                  </span>
                  <Badge theme="gray" variant="subtle" size="sm">{{ dep.status }}</Badge>
                </li>
              </ul>
            </section>

            <!-- attachments -->
            <section v-if="task.attachments?.length">
              <h3 class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
                Attachments
              </h3>
              <ul class="flex flex-col gap-1">
                <li v-for="file in task.attachments" :key="file.name">
                  <a
                    :href="file.file_url"
                    target="_blank"
                    rel="noopener"
                    class="flex items-center gap-2 rounded px-1.5 py-1 text-sm text-ink-gray-7 hover:bg-surface-gray-1"
                  >
                    <LucidePaperclip class="size-3.5 text-ink-gray-5" />
                    <span class="truncate">{{ file.file_name }}</span>
                  </a>
                </li>
              </ul>
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
  Select,
  TextEditor,
  toast,
} from 'frappe-ui'
import AssigneeSelect from './AssigneeSelect.vue'
import AvatarStack from './AvatarStack.vue'
import CreateTaskDialog from './CreateTaskDialog.vue'
import ErrorState from './ErrorState.vue'
import LogTimeDialog from './LogTimeDialog.vue'
import PriorityIcon from './PriorityIcon.vue'
import StatusPill from './StatusPill.vue'
import UserAvatar from './UserAvatar.vue'
import api from '@/data/api'
import { removeTask, upsertTask } from '@/data/board'
import { permissions, taskTypes, user } from '@/data/session'
import { statusStyle } from '@/utils/constants'
import { formatDate, formatNumber, isOverdue, plainText, timeAgo } from '@/utils/format'
import { closeTask, openTask } from '@/utils/taskPanel'

const route = useRoute()

const task = ref(null)
const loading = ref(false)
const loadError = ref(null)
const showLogTime = ref(false)
const showSubtask = ref(false)

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
const overdue = computed(() =>
  task.value ? isOverdue(task.value.exp_end_date, task.value.status) : false,
)
const hasCommentText = computed(() => Boolean(plainText(newComment.value).trim()))

const typeOptions = computed(() => [
  { label: 'No type', value: '' },
  ...taskTypes.value.map((t) => ({ label: t, value: t })),
])

const menuOptions = computed(() => [
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
