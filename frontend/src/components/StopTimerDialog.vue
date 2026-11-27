<template>
  <Dialog v-model="show" title="Log tracked time" size="md">
    <template #default>
      <div class="flex flex-col gap-3">
        <div class="rounded-6 bg-surface-gray-1 p-3">
          <p class="font-mono text-3xl tabular-nums text-ink-gray-9">
            {{ elapsedLabel }}
          </p>
          <p class="mt-0.5 text-xs text-ink-gray-5">
            {{ hours }} h will be filed against
            <span class="font-medium text-ink-gray-7">{{ task?.subject }}</span>
          </p>
        </div>

        <NullableSelect
          v-model="form.activity_type"
          label="Activity type"
          :options="activityOptions"
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
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
        <Button theme="red" variant="ghost" @click="discard">Discard timer</Button>
        <div class="flex flex-col-reverse gap-2 sm:flex-row">
          <Button @click="show = false">Keep running</Button>
          <Button variant="solid" :loading="saving" @click="submit">
            Log {{ hours }} h
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl, toast } from 'frappe-ui'
import NullableSelect from './NullableSelect.vue'
import { activityTypes } from '@/data/session'
import { cancelTimer, elapsedLabel, elapsedSeconds, stopTimer } from '@/data/timer'

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
const form = ref({ activity_type: '', description: '', is_billable: false })

const hours = computed(() => Math.max(Math.round((elapsedSeconds.value / 3600) * 100) / 100, 0.01))

const activityOptions = computed(() => activityTypes.value.map((t) => ({ label: t, value: t })))

watch(show, (open) => {
  if (!open) return
  errorMessage.value = ''
  form.value = {
    activity_type: activityTypes.value.includes('Project Work')
      ? 'Project Work'
      : activityTypes.value[0] || '',
    description: '',
    is_billable: false,
  }
})

async function submit() {
  if (!form.value.activity_type) {
    errorMessage.value = 'Pick an activity type'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await stopTimer({
      activityType: form.value.activity_type,
      description: form.value.description,
      isBillable: form.value.is_billable,
    })
    toast.success('Time logged')
    emit('logged')
    show.value = false
  } catch (e) {
    errorMessage.value = e?.messages?.join(', ') || e?.message || 'Could not log the time'
  } finally {
    saving.value = false
  }
}

function discard() {
  cancelTimer()
  show.value = false
}
</script>
