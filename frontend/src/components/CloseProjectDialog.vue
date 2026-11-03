<template>
  <Dialog v-model="show" :options="{ title: 'Close project', size: 'md' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <section>
          <label class="mb-1.5 block text-xs text-ink-gray-5">Outcome</label>
          <div class="grid gap-2 sm:grid-cols-2">
            <button
              v-for="outcome in OUTCOMES"
              :key="outcome.value"
              class="rounded-lg border p-2.5 text-left transition-colors"
              :class="
                form.status === outcome.value
                  ? 'border-outline-gray-4 bg-surface-gray-2'
                  : 'border-outline-gray-2 hover:border-outline-gray-3'
              "
              @click="form.status = outcome.value"
            >
              <p class="text-sm font-medium text-ink-gray-8">{{ outcome.label }}</p>
              <p class="mt-0.5 text-xs text-ink-gray-5">{{ outcome.hint }}</p>
            </button>
          </div>
        </section>

        <div v-if="openTasks" class="rounded-lg bg-surface-gray-1 p-3">
          <p class="text-sm text-ink-gray-8">
            {{ openTasks }} {{ openTasks === 1 ? 'task is' : 'tasks are' }} still open.
          </p>
          <FormControl
            v-model="form.cancelOpenTasks"
            class="mt-2"
            type="checkbox"
            :label="`Cancel ${openTasks === 1 ? 'it' : 'them'} too`"
            :disabled="mustCancelTasks"
          />
          <p v-if="mustCancelTasks" class="mt-1.5 text-xs text-ink-gray-5">
            This project's progress comes from task completion, so ERPNext only
            marks it completed once every task is done or cancelled.
          </p>
        </div>

        <FormControl
          v-if="permissions.canPostUpdate"
          v-model="form.note"
          type="textarea"
          label="Closing note (optional)"
          placeholder="What shipped, what didn't, and why"
          :rows="3"
        />

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button @click="show = false">Keep open</Button>
        <Button variant="solid" :loading="saving" @click="submit">
          Close as {{ form.status === 'Completed' ? 'completed' : 'cancelled' }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import api from '@/data/api'
import { projectDoc, tasks } from '@/data/board'
import { permissions } from '@/data/session'

const OUTCOMES = [
  { value: 'Completed', label: 'Completed', hint: 'The work is done.' },
  { value: 'Cancelled', label: 'Cancelled', hint: 'Stopped before it was finished.' },
]

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  project: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue', 'closed'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const saving = ref(false)
const errorMessage = ref('')
const form = ref({ status: 'Completed', cancelOpenTasks: false, note: '' })

const openTasks = computed(
  () =>
    tasks.value.filter(
      (t) => !['Completed', 'Cancelled', 'Template'].includes(t.status),
    ).length,
)

// Task Completion (ERPNext's default, also used when the field is blank) counts
// cancelled tasks as done, so cancelling the rest is what lets Completed stick.
// The other task-based methods are left to the server, which explains itself.
const mustCancelTasks = computed(
  () =>
    form.value.status === 'Completed' &&
    openTasks.value > 0 &&
    [undefined, null, '', 'Task Completion'].includes(
      projectDoc.value?.percent_complete_method,
    ),
)

// While forced the box can't be touched, so following the rule both ways never
// overrides a choice the user made.
watch(mustCancelTasks, (must) => {
  form.value.cancelOpenTasks = must
})

watch(show, (open) => {
  if (!open) return
  errorMessage.value = ''
  form.value = { status: 'Completed', cancelOpenTasks: false, note: '' }
  form.value.cancelOpenTasks = mustCancelTasks.value
})

async function submit() {
  saving.value = true
  errorMessage.value = ''
  const cancelOpenTasks = openTasks.value > 0 && form.value.cancelOpenTasks
  try {
    const doc = await api.closeProject(props.project, {
      status: form.value.status,
      note: form.value.note,
      cancelOpenTasks,
    })
    emit('closed', { doc, cancelOpenTasks })
    show.value = false
  } catch (e) {
    errorMessage.value =
      e?.messages?.join(', ') || e?.message || 'Could not close the project'
  } finally {
    saving.value = false
  }
}
</script>
