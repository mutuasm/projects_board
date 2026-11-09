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
        data-task-panel
        class="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-outline-gray-2 bg-surface-white pb-safe-bottom pt-safe-top shadow-2xl transition-[max-width] duration-200 sm:border-l"
        :class="wide ? 'sm:max-w-5xl' : 'sm:max-w-2xl'"
      >
        <!-- header -->
        <header
          class="flex shrink-0 items-center gap-1 border-b border-outline-gray-2 px-3 py-3 sm:px-5"
        >
          <button
            class="tap-target -ml-1 mr-1 grid place-items-center rounded p-1 text-ink-gray-7 hover:bg-surface-gray-2 sm:hidden"
            aria-label="Close"
            @click="close"
          >
            <LucideArrowLeft class="size-5" />
          </button>

          <button
            v-if="task"
            class="flex h-8 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg border px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60"
            :class="
              isDone
                ? 'border-transparent bg-surface-green-2 text-ink-green-3 hover:bg-surface-green-3/40'
                : 'border-outline-gray-3 text-ink-gray-8 hover:bg-surface-gray-2'
            "
            :disabled="!task.can_write || completing"
            @click="toggleComplete"
          >
            <LucideCheck class="size-4" />
            {{ isDone ? 'Completed' : 'Mark complete' }}
          </button>

          <div class="ml-auto flex items-center gap-0.5">
            <TaskTimer
              v-if="permissions.canSubmitTimesheet && task"
              :task="task"
              @logged="reload"
            />
            <Tooltip text="Copy link">
              <button class="pb-icon-btn" aria-label="Copy link" @click="copyLink">
                <LucideShare class="size-[18px]" />
              </button>
            </Tooltip>
            <Tooltip text="Attachments">
              <button
                class="pb-icon-btn"
                aria-label="Jump to attachments"
                @click="scrollTo(attachmentsSection)"
              >
                <LucidePaperclip class="size-[18px]" />
              </button>
            </Tooltip>
            <Tooltip text="Open in Desk">
              <a
                v-if="task"
                class="pb-icon-btn"
                :href="`/desk/task/${task.name}`"
                target="_blank"
                rel="noopener"
                aria-label="Open in Desk"
              >
                <LucideExternalLink class="size-[18px]" />
              </a>
            </Tooltip>
            <Tooltip :text="wide ? 'Narrow panel' : 'Widen panel'">
              <button
                class="pb-icon-btn hidden sm:grid"
                :aria-label="wide ? 'Narrow panel' : 'Widen panel'"
                @click="toggleWide"
              >
                <component :is="wide ? LucideMinimize2 : LucideMaximize2" class="size-[18px]" />
              </button>
            </Tooltip>
            <Dropdown :options="menuOptions" placement="bottom-end">
              <button class="pb-icon-btn" aria-label="More actions">
                <LucideMoreHorizontal class="size-[18px]" />
              </button>
            </Dropdown>
            <Tooltip text="Close (Esc)">
              <button class="pb-icon-btn hidden sm:grid" aria-label="Close" @click="close">
                <LucideArrowRightToLine class="size-[18px]" />
              </button>
            </Tooltip>
          </div>
        </header>

        <!-- someone else saved while you were mid-edit: don't yank the fields away -->
        <div
          v-if="remoteChanged && task"
          class="flex shrink-0 items-center gap-2 border-b border-outline-gray-2 bg-surface-amber-1 px-4 py-2 text-sm text-ink-amber-3 sm:px-6"
        >
          <LucideRefreshCw class="size-4 shrink-0" />
          <span class="flex-1">Someone else just changed this task.</span>
          <Button size="sm" @click="refreshFromRemote">Show changes</Button>
        </div>

        <div v-if="loading" class="flex flex-1 items-center justify-center">
          <LoadingIndicator class="size-5 text-ink-gray-5" />
        </div>
        <ErrorState v-else-if="loadError" :error="loadError" />

        <div
          v-else-if="task"
          ref="scroller"
          class="thin-scrollbar min-h-0 flex-1 overflow-y-auto"
        >
          <div class="flex flex-col gap-6 px-4 py-5 sm:px-6">
            <!-- title -->
            <div>
              <button
                v-if="task.epic"
                class="mb-2 flex w-fit items-center gap-1.5 text-xs font-medium text-ink-gray-6 hover:text-ink-gray-8"
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
                class="pb-title -mx-1.5 w-[calc(100%+0.75rem)] resize-none rounded-lg border border-transparent bg-transparent px-1.5 py-0.5 text-[26px] font-semibold leading-tight tracking-tight text-ink-gray-9 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none focus:ring-0"
                :readonly="!task.can_write"
                @input="autoGrow"
                @blur="saveSubject"
                @keydown.enter.prevent="$event.target.blur()"
              />
              <p class="mt-1 text-sm text-ink-gray-5">
                <span class="font-mono text-xs">{{ task.name }}</span>
                <span v-if="task.created_by">
                  · Created by {{ task.created_by.full_name }} {{ timeAgo(task.creation) }}
                </span>
              </p>
            </div>

            <!-- properties: label over value, three to a row -->
            <div class="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3">
              <div class="min-w-0">
                <p class="pb-field-label">Assignee</p>
                <AssigneeSelect
                  :model-value="assigneeEmails"
                  @update:model-value="(v) => save({ assignees: v })"
                />
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Project</p>
                <router-link
                  v-if="task.project"
                  :to="{ name: 'Board', params: { project: task.project } }"
                  class="-mx-1.5 flex min-w-0 items-center gap-2 rounded-lg px-1.5 py-1 text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-2"
                  @click="close"
                >
                  <span
                    class="grid size-6 shrink-0 place-items-center rounded-md"
                    :style="{
                      backgroundColor: `${projectColor(task.project)}26`,
                      color: projectColor(task.project),
                    }"
                  >
                    <LucideFolderKanban class="size-3.5" />
                  </span>
                  <span class="truncate">{{ task.project_title || task.project }}</span>
                </router-link>
                <span v-else class="text-sm text-ink-gray-5">No project</span>
              </div>

              <div class="col-span-2 min-w-0 sm:col-span-1">
                <p class="pb-field-label">Dates</p>
                <Popover placement="bottom-start">
                  <template #target="{ togglePopover }">
                    <button
                      class="-mx-1.5 flex min-w-0 items-center gap-2 rounded-lg px-1.5 py-1 text-left text-sm font-medium hover:bg-surface-gray-2 disabled:cursor-default disabled:hover:bg-transparent"
                      :class="overdue ? 'text-ink-red-3' : 'text-ink-gray-8'"
                      :disabled="!task.can_write"
                      @click="togglePopover()"
                    >
                      <span
                        class="grid size-6 shrink-0 place-items-center rounded-full border border-outline-gray-3 text-ink-gray-6"
                      >
                        <LucideCalendar class="size-3.5" />
                      </span>
                      <span class="truncate">{{ dateRange || 'Set dates' }}</span>
                    </button>
                  </template>
                  <template #body-main>
                    <div class="flex w-64 flex-col gap-3 p-3">
                      <FormControl
                        type="date"
                        label="Start"
                        :model-value="dateOnly(task.exp_start_date)"
                        @update:model-value="(v) => saveDate('exp_start_date', v)"
                      />
                      <FormControl
                        type="date"
                        label="Due"
                        :model-value="dateOnly(task.exp_end_date)"
                        @update:model-value="(v) => saveDate('exp_end_date', v)"
                      />
                      <Badge v-if="overdue" theme="red" variant="subtle" size="sm" class="w-fit">
                        Overdue
                      </Badge>
                    </div>
                  </template>
                </Popover>
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Status</p>
                <StatusPill
                  :status="task.status"
                  :editable="task.can_write"
                  class="-mx-2"
                  @change="(v) => save({ status: v })"
                />
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Priority</p>
                <PriorityIcon
                  :priority="task.priority"
                  :editable="task.can_write"
                  show-label
                  @change="(v) => save({ priority: v })"
                />
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Type</p>
                <NullableSelect
                  :model-value="task.type || ''"
                  :options="typeOptions"
                  variant="ghost"
                  :disabled="!task.can_write"
                  @update:model-value="(v) => save({ type: v })"
                />
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Weight</p>
                <input
                  v-model.number="draftWeight"
                  type="number"
                  step="0.5"
                  min="0"
                  :readonly="!task.can_write"
                  class="-mx-1.5 h-7 w-20 rounded border border-transparent bg-transparent px-1.5 text-sm text-ink-gray-8 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none focus:ring-0"
                  @blur="saveWeight"
                />
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Progress</p>
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
              </div>

              <div class="min-w-0">
                <p class="pb-field-label">Time</p>
                <p class="text-sm text-ink-gray-8">
                  {{ formatNumber(task.actual_time) }} h
                  <span class="text-ink-gray-5">/ {{ formatNumber(task.expected_time) }} h est.</span>
                </p>
              </div>

              <div v-if="task.status === 'Completed' || task.closing_date" class="min-w-0">
                <p class="pb-field-label">Closed on</p>
                <input
                  type="date"
                  class="-mx-1.5 h-7 rounded border border-transparent bg-transparent px-1.5 text-sm text-ink-gray-8 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none focus:ring-0"
                  :value="dateOnly(task.closing_date)"
                  :readonly="!task.can_write"
                  @change="(e) => saveDate('closing_date', e.target.value)"
                />
              </div>

              <!-- recurring: a Frappe Auto Repeat series -->
              <div
                v-if="permissions.canRepeatTasks || task.repeat"
                class="col-span-2 min-w-0 sm:col-span-3"
              >
                <p class="pb-field-label">Repeats</p>
                <div class="flex flex-wrap items-center gap-x-3 gap-y-2">
                  <span class="flex min-w-0 items-center gap-1.5 text-sm text-ink-gray-8">
                    <LucideRepeat class="size-4 shrink-0 text-ink-gray-5" />
                    <span>{{ repeatText }}</span>
                  </span>

                  <button
                    v-if="task.repeat && !task.repeat.is_template"
                    class="text-sm font-medium text-ink-gray-7 underline underline-offset-2 hover:text-ink-gray-9"
                    @click="open(task.repeat.reference_document)"
                  >
                    Open series
                  </button>

                  <template v-else-if="task.can_write && permissions.canRepeatTasks">
                    <Popover placement="bottom-start">
                      <template #target="{ togglePopover }">
                        <Button size="sm" @click="startRepeatEdit(togglePopover)">
                          {{ task.repeat ? 'Edit' : 'Make it repeat' }}
                        </Button>
                      </template>
                      <template #body-main="{ close: closePopover }">
                        <div class="flex w-80 flex-col gap-3 p-3">
                          <RepeatEditor v-model="repeatDraft" :anchor="repeatAnchor" />
                          <ErrorMessage :message="repeatError" />
                          <div class="flex justify-end gap-2">
                            <Button @click="closePopover()">Cancel</Button>
                            <Button
                              variant="solid"
                              :loading="savingRepeat"
                              @click="saveRepeat(closePopover)"
                            >
                              Save
                            </Button>
                          </div>
                        </div>
                      </template>
                    </Popover>
                    <Button
                      v-if="task.repeat"
                      size="sm"
                      variant="ghost"
                      :loading="savingRepeat"
                      @click="stopRepeat"
                    >
                      Stop repeating
                    </Button>
                  </template>
                </div>
              </div>

              <div class="col-span-2 min-w-0 sm:col-span-3">
                <p class="pb-field-label">Labels</p>
                <TagInput
                  :model-value="task.tags || []"
                  :readonly="!task.can_write"
                  @update:model-value="saveTags"
                />
              </div>
            </div>

            <!-- review: ERPNext keeps an in-review task from going Overdue until its review date -->
            <div
              v-if="task.status === 'Pending Review'"
              class="pb-panel flex flex-col gap-3 p-3 sm:flex-row sm:items-center"
            >
              <div class="flex min-w-0 flex-1 items-start gap-2.5">
                <LucideClipboardCheck class="mt-0.5 size-4 shrink-0 text-ink-amber-3" />
                <div class="min-w-0">
                  <p class="text-sm font-medium text-ink-gray-9">In review</p>
                  <p class="text-xs" :class="reviewHint.class">{{ reviewHint.text }}</p>
                </div>
              </div>
              <label class="flex shrink-0 items-center gap-2 text-xs text-ink-gray-6">
                Review by
                <input
                  type="date"
                  class="pb-input h-8 px-2 text-sm"
                  :value="dateOnly(task.review_date)"
                  :readonly="!task.can_write"
                  @change="(e) => saveDate('review_date', e.target.value)"
                />
              </label>
              <div v-if="task.can_write" class="flex shrink-0 gap-2">
                <Button size="sm" :loading="completing" @click="setStatus('Working')">
                  Send back
                </Button>
                <Button size="sm" variant="solid" :loading="completing" @click="setStatus('Completed')">
                  <template #prefix><LucideCheck class="size-3.5" /></template>
                  Approve
                </Button>
              </div>
            </div>

            <hr class="border-outline-gray-2" />

            <!-- description -->
            <section>
              <h3 class="pb-section-title">Description</h3>
              <TextEditor
                :key="`desc-${task.name}`"
                editor-class="prose-f min-h-16 -mx-2.5 rounded-lg border border-transparent px-2.5 py-2 text-ink-gray-7 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none"
                :content="task.description || ''"
                :editable="task.can_write"
                placeholder="Add a description…"
                @blur="saveDescription"
                @change="(value) => (draftDescription = value)"
              />
            </section>

            <!-- child tasks -->
            <section v-if="task.subtasks?.length || task.is_group">
              <div class="mb-2 flex items-center gap-2">
                <h3 class="pb-section-title !mb-0">Child tasks</h3>
                <span
                  v-if="task.subtask_progress?.total"
                  class="text-xs tabular-nums text-ink-gray-5"
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
                  Add child task
                </Button>
              </div>
              <ul class="flex flex-col divide-y divide-outline-gray-1">
                <li
                  v-for="sub in task.subtasks"
                  :key="sub.name"
                  class="flex cursor-pointer items-center gap-2 py-2 hover:bg-surface-gray-1"
                  @click="open(sub.name)"
                >
                  <span class="size-1.5 rounded-full" :class="statusStyle(sub.status).dot" />
                  <span class="flex-1 truncate text-sm text-ink-gray-8">
                    {{ sub.subject }}
                  </span>
                  <AvatarStack :users="sub.assignees || []" :max="2" size="xs" />
                </li>
                <li v-if="!task.subtasks?.length" class="py-2 text-xs text-ink-gray-4">
                  No child tasks yet.
                </li>
              </ul>
            </section>

            <!-- dependencies (native Task Depends On) -->
            <section>
              <h3 class="pb-section-title">Blocked by</h3>
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
              <h3 class="pb-section-title">Blocks</h3>
              <ul class="flex flex-col divide-y divide-outline-gray-1">
                <li
                  v-for="dep in task.blocks"
                  :key="dep.name"
                  class="flex cursor-pointer items-center gap-2 py-2 hover:bg-surface-gray-1"
                  @click="open(dep.name)"
                >
                  <span class="size-1.5 rounded-full" :class="statusStyle(dep.status).dot" />
                  <span class="flex-1 truncate text-sm text-ink-gray-8">{{ dep.subject }}</span>
                </li>
              </ul>
            </section>

            <!-- attachments -->
            <section ref="attachmentsSection">
              <h3 class="pb-section-title">Attachments</h3>
              <TaskAttachments
                :files="task.attachments || []"
                :task="task.name"
                :readonly="!task.can_write"
                @change="(files) => (task.attachments = files)"
              />
            </section>

            <!-- comments and the full activity feed -->
            <section>
              <div class="mb-4 flex items-center gap-6 border-b border-outline-gray-2">
                <button
                  v-for="tab in activityTabs"
                  :key="tab.value"
                  class="-mb-px flex items-center gap-1.5 border-b-2 pb-2.5 text-[15px] transition-colors"
                  :class="
                    activityTab === tab.value
                      ? 'border-ink-gray-9 font-medium text-ink-gray-9'
                      : 'border-transparent text-ink-gray-6 hover:text-ink-gray-9'
                  "
                  @click="activityTab = tab.value"
                >
                  {{ tab.label }}
                  <span
                    v-if="tab.count"
                    class="rounded-full bg-surface-gray-2 px-1.5 text-xs tabular-nums text-ink-gray-6"
                  >
                    {{ tab.count }}
                  </span>
                </button>
              </div>

              <!-- comments -->
              <ul v-if="activityTab === 'comments'" class="mb-4 flex flex-col gap-4">
                <li v-for="comment in task.comments" :key="comment.name" class="flex gap-3">
                  <UserAvatar
                    :user="{ full_name: comment.full_name, user_image: comment.user_image }"
                    size="xl"
                  />
                  <div class="min-w-0 flex-1">
                    <div class="flex items-baseline gap-2">
                      <span class="text-sm font-medium text-ink-gray-9">
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
                <li v-if="!task.comments?.length" class="text-sm text-ink-gray-5">
                  No comments yet. Start the conversation below.
                </li>
              </ul>

              <!-- everything, oldest first -->
              <ol v-else class="mb-4 flex flex-col">
                <li
                  v-for="(item, index) in activity"
                  :key="item.key"
                  class="relative flex gap-3 pb-4 last:pb-0"
                >
                  <span
                    v-if="index < activity.length - 1"
                    class="absolute bottom-0 left-[15px] top-9 w-px bg-outline-gray-3"
                  />
                  <UserAvatar :user="item.user" size="xl" class="relative" />
                  <div class="min-w-0 flex-1 pt-1 text-sm text-ink-gray-6">
                    <p>
                      <span class="font-medium text-ink-gray-9">{{ item.user.full_name }}</span>
                      <template v-if="item.kind === 'created'"> created this task</template>
                      <template v-else-if="item.kind === 'comment'"> commented</template>
                      <template v-else-if="item.kind === 'time'">
                        logged
                        <span class="font-medium text-ink-gray-8">{{ formatNumber(item.hours) }} h</span>
                        <template v-if="item.note"> · {{ item.note }}</template>
                      </template>
                      <template v-else>
                        <span v-for="(change, i) in item.changes" :key="i">
                          changed {{ change.field }} from
                          <span class="text-ink-gray-8">{{ change.from || '—' }}</span>
                          to
                          <span class="text-ink-gray-8">{{ change.to || '—' }}</span
                          ><span v-if="i < item.changes.length - 1">, </span>
                        </span>
                      </template>
                      <span class="text-ink-gray-4"> · {{ timeAgo(item.at) }}</span>
                    </p>
                    <div
                      v-if="item.kind === 'comment'"
                      class="prose-f mt-1.5 rounded-lg bg-surface-gray-1 px-3 py-2 text-sm"
                      v-html="item.content"
                    />
                  </div>
                </li>
              </ol>

              <!-- composer -->
              <div class="flex gap-3">
                <UserAvatar :user="user" size="xl" />
                <div
                  class="min-w-0 flex-1 rounded-xl border border-outline-gray-2 transition-colors focus-within:border-outline-gray-4"
                  @keydown.meta.enter.prevent="postComment"
                  @keydown.ctrl.enter.prevent="postComment"
                >
                  <TextEditor
                    ref="commentEditor"
                    :key="`comment-${task.name}-${commentKey}`"
                    editor-class="prose-f min-h-14 px-3 pt-2.5 pb-1 focus:outline-none"
                    content=""
                    placeholder="Write a comment…"
                    @change="(value) => (newComment = value)"
                  />
                  <div class="flex items-center gap-2 px-2 pb-2">
                    <span class="hidden px-1 text-xs text-ink-gray-4 sm:inline">
                      {{ sendHint }} to send
                    </span>
                    <Button
                      variant="solid"
                      size="sm"
                      class="ml-auto"
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
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Popover,
  TextEditor,
  Tooltip,
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
import RepeatEditor from './RepeatEditor.vue'
import StatusPill from './StatusPill.vue'
import UserAvatar from './UserAvatar.vue'
import api from '@/data/api'
import { removeTask, upsertTask } from '@/data/board'
import { permissions, taskTypes, user } from '@/data/session'
import { isNarrow } from '@/data/ui'
import { projectColor, statusStyle } from '@/utils/constants'
import { dayjs, formatNumber, isOverdue, plainText, timeAgo } from '@/utils/format'
import { closeTask, escapeTargetsPanel, openTask } from '@/utils/taskPanel'
import { describeRepeat } from '@/utils/repeat'
import { watchDoc } from '@/data/realtime'

import LucideMaximize2 from '~icons/lucide/maximize-2'
import LucideMinimize2 from '~icons/lucide/minimize-2'

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
const completing = ref(false)
const scroller = ref(null)
const attachmentsSection = ref(null)
const activityTab = ref('comments')

/** The wider panel is a per-user preference, like the sidebar's collapse. */
const wide = ref(readPref('pb:panel-wide') === '1')

function readPref(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function toggleWide() {
  wide.value = !wide.value
  try {
    localStorage.setItem('pb:panel-wide', wide.value ? '1' : '0')
  } catch {
    // private mode: the toggle still works for this session
  }
}

const sendHint = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘↵' : 'Ctrl+↵'

const remoteChanged = ref(false)

const repeatDraft = ref(null)
const repeatError = ref('')
const savingRepeat = ref(false)

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

const isDone = computed(() => task.value?.status === 'Completed')

const repeatAnchor = computed(
  () =>
    task.value?.repeat?.start_date ||
    dateOnly(task.value?.exp_start_date) ||
    dateOnly(task.value?.exp_end_date),
)

const repeatText = computed(() => {
  const r = task.value?.repeat
  if (!r) return "Doesn't repeat"
  const rule = describeRepeat(r, r.start_date)
  if (!r.is_template) {
    return r.disabled
      ? `From the series “${r.template_subject}”, which has stopped`
      : `One occurrence of “${r.template_subject}” · ${rule}`
  }
  return r.next_schedule_date
    ? `${rule} · next copy ${dayjs(r.next_schedule_date).format('D MMM')}`
    : rule
})

const reviewHint = computed(() => {
  const t = task.value
  if (!t?.review_date) {
    return t?.exp_end_date
      ? {
          text: 'Set a review date - without one, ERPNext marks it Overdue once the due date passes.',
          class: 'text-ink-amber-3',
        }
      : { text: 'Waiting for sign-off. A review date sets when it is due.', class: 'text-ink-gray-5' }
  }
  if (dayjs(t.review_date).isBefore(dayjs().startOf('day'))) {
    return { text: `Review was due ${dayjs(t.review_date).format('D MMM')}.`, class: 'text-ink-red-3' }
  }
  return {
    text: `Due for review ${dayjs(t.review_date).format('D MMM')} - it won't go Overdue before then.`,
    class: 'text-ink-gray-5',
  }
})

/** "21 Apr → 24 Apr, 2026", dropping the repeated year when both share one. */
const dateRange = computed(() => {
  const start = task.value?.exp_start_date && dayjs(task.value.exp_start_date)
  const end = task.value?.exp_end_date && dayjs(task.value.exp_end_date)
  if (start && end) {
    const sameYear = start.year() === end.year()
    return `${start.format(sameYear ? 'D MMM' : 'D MMM YYYY')} → ${end.format('D MMM, YYYY')}`
  }
  if (end) return `Due ${end.format('D MMM, YYYY')}`
  if (start) return `From ${start.format('D MMM, YYYY')}`
  return ''
})

/** Creation, comments, field changes and time logs on one oldest-first line. */
const activity = computed(() => {
  const t = task.value
  if (!t) return []
  const person = (name, image) => ({ full_name: name, user_image: image })
  const items = [
    {
      key: 'created',
      kind: 'created',
      at: t.creation,
      user: t.created_by || person(t.owner),
    },
    ...(t.comments || []).map((c) => ({
      key: `c-${c.name}`,
      kind: 'comment',
      at: c.creation,
      user: person(c.full_name, c.user_image),
      content: c.content,
    })),
    ...(t.history || []).map((h) => ({
      key: `h-${h.name}`,
      kind: 'change',
      at: h.creation,
      user: person(h.full_name, h.user_image),
      changes: h.changes,
    })),
    ...(t.time_logs || []).map((log) => ({
      key: `t-${log.name}`,
      kind: 'time',
      at: log.from_time,
      user: person(log.logged_by || 'Someone'),
      hours: log.hours,
      note: log.description || log.activity_type,
    })),
  ]
  return items.sort((a, b) => dayjs(a.at).valueOf() - dayjs(b.at).valueOf())
})

const activityTabs = computed(() => [
  { value: 'comments', label: 'Comments', count: task.value?.comments?.length || 0 },
  { value: 'activity', label: 'All activity', count: 0 },
])

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
  ...(task.value?.can_delete
    ? [{ label: 'Delete task', icon: 'trash-2', onClick: destroy }]
    : []),
])

function close() {
  closeTask()
}

function startRepeatEdit(toggle) {
  const r = task.value?.repeat
  repeatDraft.value = r
    ? {
        frequency: r.frequency,
        repeat_on_days: [...(r.repeat_on_days || [])],
        repeat_on_last_day: r.repeat_on_last_day,
        end_date: r.end_date ? dateOnly(r.end_date) : '',
      }
    : null
  repeatError.value = ''
  toggle()
}

async function saveRepeat(closePopover) {
  if (!repeatDraft.value) {
    // "Doesn't repeat" chosen in the editor
    if (task.value.repeat) await stopRepeat()
    closePopover()
    return
  }
  savingRepeat.value = true
  repeatError.value = ''
  try {
    task.value.repeat = await api.setTaskRepeat(task.value.name, repeatDraft.value)
    toast.success('Repeat saved')
    closePopover()
  } catch (e) {
    repeatError.value = e?.messages?.join(', ') || e?.message || 'Could not save the repeat'
  } finally {
    savingRepeat.value = false
  }
}

async function stopRepeat() {
  savingRepeat.value = true
  try {
    await api.stopTaskRepeat(task.value.name)
    task.value.repeat = null
    toast.success('Stopped repeating - copies already made stay')
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not stop the repeat')
  } finally {
    savingRepeat.value = false
  }
}

function copyLink() {
  navigator.clipboard?.writeText(window.location.href)
  toast.success('Link copied')
}

function scrollTo(el) {
  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function toggleComplete() {
  return setStatus(isDone.value ? 'Open' : 'Completed')
}

/** Same path as dropping a card in a board column, so completion gets stamped. */
async function setStatus(status) {
  if (!task.value?.can_write) return
  completing.value = true
  try {
    const row = await api.moveTask(task.value.name, status)
    upsertTask(row)
    await reload()
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not update the task')
  } finally {
    completing.value = false
  }
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

/** A silent load refreshes in place, keeping the scroll position. */
async function load(name, { silent = false } = {}) {
  if (!silent) loading.value = true
  loadError.value = null
  try {
    task.value = await api.getTask(name)
    remoteChanged.value = false
    syncDrafts()
  } catch (e) {
    loadError.value = e
    task.value = null
  } finally {
    loading.value = false
  }
}

async function reload() {
  if (taskName.value) await load(taskName.value, { silent: true })
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

/**
 * A native date input reports the same value more than once (input, then
 * change). Record it locally first so the repeat is a no-op instead of a
 * second save racing the first on the same row.
 */
function saveDate(field, value) {
  const next = value || null
  if (next === (dateOnly(task.value[field]) || null)) return
  task.value[field] = next
  save({ [field]: next })
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

/**
 * Live edits from other people (or the desk). A new comment just refreshes the
 * thread; a field change refreshes the task - unless you are typing in the
 * panel, in which case it asks first instead of overwriting your edit.
 */
let stopWatching = null
watch(
  taskName,
  (name) => {
    stopWatching?.()
    remoteChanged.value = false
    stopWatching = name ? watchDoc('Task', name, onRemoteChange) : null
  },
  { immediate: true },
)
onUnmounted(() => stopWatching?.())

async function onRemoteChange(event, data) {
  if (!task.value) return
  if (event === 'docinfo_update') {
    if (data?.key === 'comments') {
      task.value.comments = (await api.getComments('Task', task.value.name)) || []
    } else {
      await reload()
    }
    return
  }
  // our own save already put this version on screen
  if (data?.modified && String(data.modified) === String(task.value.modified)) return
  if (isEditingInPanel()) {
    remoteChanged.value = true
    return
  }
  await reload()
}

function isEditingInPanel() {
  const el = document.activeElement
  if (!el?.closest?.('[data-task-panel]')) return false
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) || el.isContentEditable
}

async function refreshFromRemote() {
  remoteChanged.value = false
  await reload()
}

// Esc closes the panel, like every other issue tracker.
function onKeydown(event) {
  if (
    event.key === 'Escape' &&
    taskName.value &&
    !showLogTime.value &&
    !showSubtask.value &&
    escapeTargetsPanel(event)
  ) {
    close()
  }
}
window.addEventListener('keydown', onKeydown)
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>
