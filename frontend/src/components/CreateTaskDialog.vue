<template>
  <Dialog
    v-model="show"
    :options="{ title: dialogTitle, size: 'xl' }"
  >
    <template #body-content>
      <div class="thin-scrollbar flex max-h-[70vh] flex-col gap-3 overflow-y-auto sm:max-h-none sm:overflow-visible">
        <FormControl
          ref="subjectInput"
          v-model="form.subject"
          label="Subject"
          placeholder="What needs to be done?"
          required
          @keydown.enter="submit"
        />

        <!-- opened outside a project (e.g. from My Work): let the user pick one -->
        <NullableSelect
          v-if="!project"
          v-model="form.project"
          label="Project"
          :options="projectOptions"
        />

        <!-- only epics (group tasks) can hold other tasks; ERPNext enforces it on save -->
        <div v-if="targetProject">
          <NullableSelect
            v-model="form.parent_task"
            label="Parent task"
            :options="parentOptions"
            :disabled="loadingParents"
          />
          <p v-if="!loadingParents && !openEpics.length" class="mt-1 text-xs text-ink-gray-5">
            This project has no epics yet. Tick "Epic" on a task to group others under it.
          </p>
        </div>

        <div>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Description</label>
          <TextEditor
            editor-class="prose-f max-h-40 min-h-20 overflow-y-auto rounded border border-outline-gray-2 px-2 py-1.5 focus:outline-none sm:max-h-56 sm:min-h-24"
            :content="form.description"
            placeholder="Add more detail…"
            @change="(value) => (form.description = value)"
          />
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <FormControl
            v-model="form.status"
            type="select"
            label="Status"
            :options="statusOptions"
          />
          <FormControl
            v-model="form.priority"
            type="select"
            label="Priority"
            :options="taskPriorities"
          />
          <NullableSelect v-model="form.type" label="Type" :options="typeOptions" />
          <FormControl
            v-model.number="form.task_weight"
            type="number"
            label="Weight (points)"
            placeholder="0"
          />
          <FormControl
            v-model="form.exp_start_date"
            type="date"
            label="Start date"
          />
          <FormControl
            v-model="form.exp_end_date"
            type="date"
            label="Due date"
          />
        </div>

        <!-- a Frappe Auto Repeat series, with this task as its first occurrence -->
        <RepeatEditor
          v-if="permissions.canRepeatTasks"
          v-model="form.repeat"
          :anchor="form.exp_start_date || form.exp_end_date"
        />
        <!-- not silently missing: say why, and let an admin fix it here -->
        <div
          v-else
          class="flex flex-wrap items-center gap-2 rounded-lg bg-surface-gray-1 px-3 py-2 text-xs text-ink-gray-6"
        >
          <LucideRepeat class="size-3.5 shrink-0" />
          <span class="min-w-0 flex-1">
            Repeating tasks aren't switched on for this site yet.
            <template v-if="!permissions.isSystemManager">Ask your administrator.</template>
          </span>
          <Button
            v-if="permissions.isSystemManager"
            size="sm"
            :loading="enablingRepeat"
            @click="enableRepeat"
          >
            Switch on
          </Button>
        </div>

        <div>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Assignees</label>
          <AssigneeSelect v-model="form.assignees" />
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <FormControl v-model="form.is_milestone" type="checkbox" label="Milestone" />
          <FormControl v-model="form.is_group" type="checkbox" label="Epic (can hold child tasks)" />
          <label v-if="form.is_group" class="flex items-center gap-2 text-sm text-ink-gray-7">
            Colour
            <input
              v-model="form.color"
              type="color"
              class="h-7 w-10 cursor-pointer rounded border border-outline-gray-2 bg-transparent p-0.5"
            />
          </label>
        </div>

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button @click="show = false">Cancel</Button>
        <Button variant="solid" :loading="saving" @click="submit">
          Create task
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl, TextEditor } from 'frappe-ui'
import AssigneeSelect from './AssigneeSelect.vue'
import NullableSelect from './NullableSelect.vue'
import RepeatEditor from './RepeatEditor.vue'
import api from '@/data/api'
import { projects } from '@/data/projects'
import {
  boardStatuses,
  permissions,
  session,
  taskPriorities,
  taskTypes,
  user,
} from '@/data/session'
import { statusStyle } from '@/utils/constants'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  project: { type: String, default: null },
  defaultStatus: { type: String, default: 'Open' },
  defaultParent: { type: String, default: null },
  defaultIsGroup: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const saving = ref(false)
const errorMessage = ref('')
const subjectInput = ref(null)
const enablingRepeat = ref(false)

/** Same switch `bench migrate` flips; then re-read the boot so the editor appears. */
async function enableRepeat() {
  enablingRepeat.value = true
  errorMessage.value = ''
  try {
    await api.enableRepeatingTasks()
    await session.boot.reload()
  } catch (e) {
    errorMessage.value =
      e?.messages?.join(', ') || e?.message || 'Could not switch on repeating tasks'
  } finally {
    enablingRepeat.value = false
  }
}

function blankForm() {
  return {
    subject: '',
    description: '',
    status: props.defaultStatus || 'Open',
    priority: 'Medium',
    type: '',
    task_weight: null,
    exp_start_date: '',
    exp_end_date: '',
    assignees: [],
    project: '',
    repeat: null,
    parent_task: props.defaultParent || '',
    is_milestone: false,
    color: '#3b82f6',
    is_group: props.defaultIsGroup || false,
  }
}

const form = ref(blankForm())

const statusOptions = computed(() =>
  boardStatuses.value.map((s) => ({
    label: statusStyle(s).label || s,
    value: s,
  })),
)

const typeOptions = computed(() => [
  { label: 'No type', value: '' },
  ...taskTypes.value.map((t) => ({ label: t, value: t })),
])

const projectOptions = computed(() => [
  { label: 'No project', value: '' },
  ...projects.value
    .filter((p) => ['Open', 'On hold'].includes(p.status))
    .map((p) => ({ label: p.project_name, value: p.name })),
])

const dialogTitle = computed(() => {
  if (props.defaultIsGroup) return 'New epic'
  return props.defaultParent ? 'New child task' : 'New task'
})

/** The project the task will land in: fixed by the page, or picked in the form. */
const targetProject = computed(() => props.project || form.value.project || '')

// Fetched rather than read from the board store, which only holds the project
// last opened and is empty when the dialog is opened from My Work.
const epics = ref([])
const loadingParents = ref(false)
let epicsRequest = 0

async function loadParents(project) {
  const request = ++epicsRequest
  epics.value = []
  if (!project) return
  loadingParents.value = true
  try {
    const rows = (await api.getProjectEpics(project)) || []
    if (request === epicsRequest) epics.value = rows
  } catch {
    // no list to pick from; the task can still be created at the top level
  } finally {
    if (request === epicsRequest) loadingParents.value = false
  }
}

// ERPNext won't put an open task under a completed parent, so closed epics are
// left out - except the one the dialog was opened from, which stays selectable.
const openEpics = computed(() =>
  epics.value.filter(
    (e) => !['Completed', 'Cancelled'].includes(e.status) || e.name === props.defaultParent,
  ),
)

const parentOptions = computed(() => [
  { label: 'None (top level)', value: '' },
  ...openEpics.value.map((e) => ({ label: e.subject, value: e.name })),
])

watch(
  () => [show.value, targetProject.value],
  ([open, project], previous) => {
    if (!open) return
    // a different project has different epics
    if (previous?.[0] && previous[1] !== project) form.value.parent_task = ''
    loadParents(project)
  },
)

watch(show, async (open) => {
  if (!open) return
  errorMessage.value = ''
  form.value = blankForm()
  // Assigning to yourself is the common case; still one click to remove.
  form.value.assignees = user.value?.name ? [user.value.name] : []
  await nextTick()
  subjectInput.value?.$el?.querySelector('input')?.focus()
})

async function submit() {
  if (!form.value.subject.trim()) {
    errorMessage.value = 'Subject is required'
    return
  }

  saving.value = true
  errorMessage.value = ''

  try {
    const payload = {
      ...form.value,
      project: props.project || form.value.project || null,
      is_milestone: form.value.is_milestone ? 1 : 0,
      is_group: form.value.is_group ? 1 : 0,
      // only epics carry a colour; it is what tints their chip on every card
      color: form.value.is_group ? form.value.color : '',
      task_weight: form.value.task_weight || 0,
      repeat: form.value.repeat ? JSON.stringify(form.value.repeat) : '',
    }
    const task = await api.createTask(payload)
    emit('created', task)
    show.value = false
  } catch (e) {
    errorMessage.value =
      e?.messages?.join(', ') || e?.message || 'Could not create the task'
  } finally {
    saving.value = false
  }
}
</script>
