<template>
  <Dialog v-model="show" title="New project" size="lg">
    <template #default>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="form.project_name"
          label="Project name"
          placeholder="e.g. Website revamp"
          required
          @keydown.enter="submit"
        />

        <!-- native Project Template: ERPNext copies the template's tasks in -->
        <section v-if="templates.length">
          <label class="mb-1.5 block text-xs text-ink-gray-5">Start from a template</label>
          <div class="grid gap-2 sm:grid-cols-2">
            <button
              v-for="template in templateChoices"
              :key="template.value"
              class="rounded-6 border p-2.5 text-left transition-colors"
              :class="
                form.project_template === template.value
                  ? 'border-outline-gray-4 bg-surface-gray-2'
                  : 'border-outline-gray-2 hover:border-outline-gray-3'
              "
              @click="form.project_template = template.value"
            >
              <p class="text-sm-medium text-ink-gray-8">{{ template.label }}</p>
              <p class="mt-0.5 text-xs text-ink-gray-5">{{ template.hint }}</p>
            </button>
          </div>
        </section>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
          <NullableSelect
            v-model="form.project_type"
            label="Type"
            :options="typeOptions"
          />
          <FormControl
            v-model="form.percent_complete_method"
            type="select"
            label="% Complete method"
            :options="methodOptions"
          />
          <DateField v-model="form.expected_start_date" label="Expected start" />
          <DateField v-model="form.expected_end_date" label="Expected end" />
        </div>

        <div>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Team</label>
          <AssigneeSelect v-model="form.members" />
        </div>

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
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
import NullableSelect from './NullableSelect.vue'
import DateField from './DateField.vue'
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
    project_template: '',
    expected_start_date: '',
    expected_end_date: '',
    members: user.value?.name ? [user.value.name] : [],
  }
}

const form = ref(blankForm())
const templates = ref([])

const templateChoices = computed(() => [
  { value: '', label: 'Blank project', hint: 'Start with no tasks' },
  ...templates.value.map((t) => ({
    value: t.name,
    label: t.name,
    hint: t.task_count
      ? `${t.task_count} tasks · ${t.sample_tasks.slice(0, 2).join(', ')}…`
      : 'No tasks defined',
  })),
])

const priorityOptions = computed(() => options.value.project_priorities || [])
const typeOptions = computed(() => [
  { label: 'No type', value: '' },
  ...projectTypes.value.map((t) => ({ label: t, value: t })),
])
const methodOptions = computed(() => options.value.percent_complete_methods || [])

watch(show, async (open) => {
  if (!open) return
  errorMessage.value = ''
  form.value = blankForm()
  if (!templates.value.length) {
    templates.value = (await api.getProjectTemplates()) || []
  }
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
