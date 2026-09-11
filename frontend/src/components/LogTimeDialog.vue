<template>
  <Dialog v-model="show" :options="{ title: 'Log time', size: 'md' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p class="text-sm text-ink-gray-6">
          Creates a native Timesheet entry against
          <span class="font-medium text-ink-gray-8">{{ task?.subject }}</span>.
        </p>

        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model.number="form.hours"
            type="number"
            step="0.25"
            label="Hours"
            placeholder="1.5"
          />
          <FormControl v-model="form.from_time" type="datetime-local" label="From" />
        </div>

        <FormControl
          v-model="form.activity_type"
          type="select"
          label="Activity type"
          required
          :options="activityOptions"
          description="ERPNext requires an activity type on a submitted timesheet."
        />

        <FormControl
          v-model="form.description"
          type="textarea"
          label="What did you work on?"
          :rows="3"
        />

        <FormControl v-model="form.is_billable" type="checkbox" label="Billable" />

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button @click="show = false">Cancel</Button>
        <Button variant="solid" :loading="saving" @click="submit">Log time</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl, toast } from 'frappe-ui'
import api from '@/data/api'
import { activityTypes } from '@/data/session'
import { dayjs } from '@/utils/format'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  task: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'logged'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const saving = ref(false)
const errorMessage = ref('')

const activityOptions = computed(() =>
  activityTypes.value.map((t) => ({ label: t, value: t })),
)

/** Prefer a generic activity if the site defines one. */
function defaultActivityType() {
  const list = activityTypes.value
  return list.find((t) => t === 'Project Work') || list[0] || ''
}

function blankForm() {
  return {
    hours: 1,
    from_time: dayjs().format('YYYY-MM-DDTHH:mm'),
    activity_type: defaultActivityType(),
    description: '',
    is_billable: false,
  }
}

const form = ref(blankForm())

watch(show, (open) => {
  if (!open) return
  errorMessage.value = ''
  form.value = blankForm()
})

async function submit() {
  if (!form.value.hours || form.value.hours <= 0) {
    errorMessage.value = 'Enter the hours worked'
    return
  }
  if (!form.value.activity_type) {
    errorMessage.value = 'Pick an activity type'
    return
  }

  saving.value = true
  errorMessage.value = ''

  try {
    await api.logTime({
      task: props.task.name,
      hours: form.value.hours,
      description: form.value.description,
      from_time: form.value.from_time
        ? dayjs(form.value.from_time).format('YYYY-MM-DD HH:mm:ss')
        : null,
      activity_type: form.value.activity_type,
      is_billable: form.value.is_billable ? 1 : 0,
      submit: 1,
    })
    toast.success('Time logged')
    emit('logged')
    show.value = false
  } catch (e) {
    errorMessage.value =
      e?.messages?.join(', ') || e?.message || 'Could not log time'
  } finally {
    saving.value = false
  }
}
</script>
