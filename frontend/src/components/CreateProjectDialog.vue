<template>
  <Dialog v-model="show" :options="{ title: 'New project', size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="form.project_name"
          label="Project name"
          placeholder="e.g. Website revamp"
          required
          @keydown.enter="submit"
        />

        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.status"
            type="select"
            label="Status"
            :options="projectStatuses"
          />
          <FormControl
            v-model="form.priority"
            type="select"
            label="Priority"
            :options="priorityOptions"
          />
          <FormControl
            v-model="form.project_type"
            type="select"
            label="Type"
            :options="typeOptions"
          />
          <FormControl
            v-model="form.percent_complete_method"
            type="select"
            label="% Complete method"
            :options="methodOptions"
          />
          <FormControl
            v-model="form.expected_start_date"
            type="date"
            label="Expected start"
          />
          <FormControl
            v-model="form.expected_end_date"
            type="date"
            label="Expected end"
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Team</label>
          <AssigneeSelect v-model="form.members" />
        </div>

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button @click="show = false">Cancel</Button>
        <Button variant="solid" :loading="saving" @click="submit">
          Create project
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import AssigneeSelect from './AssigneeSelect.vue'
import api from '@/data/api'
import { options, projectStatuses, projectTypes, user } from '@/data/session'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'created'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const saving = ref(false)
const errorMessage = ref('')

function blankForm() {
  return {
    project_name: '',
    status: 'Open',
    priority: 'Medium',
    project_type: '',
    percent_complete_method: 'Task Completion',
    expected_start_date: '',
    expected_end_date: '',
    members: user.value?.name ? [user.value.name] : [],
  }
}

const form = ref(blankForm())

const priorityOptions = computed(() => options.value.project_priorities || [])
const typeOptions = computed(() => [
  { label: 'No type', value: '' },
  ...projectTypes.value.map((t) => ({ label: t, value: t })),
])
const methodOptions = computed(() => options.value.percent_complete_methods || [])

watch(show, (open) => {
  if (!open) return
  errorMessage.value = ''
  form.value = blankForm()
})

async function submit() {
  if (!form.value.project_name.trim()) {
    errorMessage.value = 'Project name is required'
    return
  }

  saving.value = true
  errorMessage.value = ''

  try {
    const name = await api.createProject({ ...form.value })
    emit('created', name)
    show.value = false
  } catch (e) {
    errorMessage.value =
      e?.messages?.join(', ') || e?.message || 'Could not create the project'
  } finally {
    saving.value = false
  }
}
</script>
