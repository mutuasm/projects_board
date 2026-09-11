<template>
  <Dialog
    v-model="show"
    :options="{ title: 'New task', size: 'xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          ref="subjectInput"
          v-model="form.subject"
          label="Subject"
          placeholder="What needs to be done?"
          required
          @keydown.enter="submit"
        />

        <div>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Description</label>
          <TextEditor
            editor-class="prose-f min-h-24 max-h-56 overflow-y-auto rounded border border-outline-gray-2 px-2 py-1.5 focus:outline-none"
            :content="form.description"
            placeholder="Add more detail…"
            @change="(value) => (form.description = value)"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
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
          <FormControl
            v-model="form.type"
            type="select"
            label="Type"
            :options="typeOptions"
          />
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

        <div>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Assignees</label>
          <AssigneeSelect v-model="form.assignees" />
        </div>

        <FormControl
          v-if="groupTaskOptions.length > 1"
          v-model="form.parent_task"
          type="select"
          label="Parent task (epic)"
          :options="groupTaskOptions"
        />

        <div class="flex items-center gap-4">
          <FormControl v-model="form.is_milestone" type="checkbox" label="Milestone" />
          <FormControl v-model="form.is_group" type="checkbox" label="Epic (can hold subtasks)" />
        </div>

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
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
import api from '@/data/api'
import { tasks } from '@/data/board'
import { boardStatuses, taskPriorities, taskTypes, user } from '@/data/session'
import { statusStyle } from '@/utils/constants'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  project: { type: String, default: null },
  defaultStatus: { type: String, default: 'Open' },
  defaultParent: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const saving = ref(false)
const errorMessage = ref('')
const subjectInput = ref(null)

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
    parent_task: props.defaultParent || '',
    is_milestone: false,
    is_group: false,
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

/** Only group tasks can be a parent - ERPNext enforces this on save. */
const groupTaskOptions = computed(() => [
  { label: 'No parent', value: '' },
  ...tasks.value
    .filter((t) => t.is_group)
    .map((t) => ({ label: t.subject, value: t.name })),
])

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
      project: props.project,
      is_milestone: form.value.is_milestone ? 1 : 0,
      is_group: form.value.is_group ? 1 : 0,
      task_weight: form.value.task_weight || 0,
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
