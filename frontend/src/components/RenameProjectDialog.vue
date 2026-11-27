<template>
  <Dialog v-model="show" title="Rename project" size="sm">
    <template #default>
      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <FormControl
          ref="input"
          v-model="name"
          label="Project name"
          :maxlength="140"
          autocomplete="off"
        />
        <!-- links and task numbers use the ID, so they keep working after a rename -->
        <p class="text-xs text-ink-gray-5">
          The project ID stays {{ project }}, so links and tasks are unaffected.
        </p>
        <ErrorMessage :message="errorMessage" />
      </form>
    </template>

    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button @click="show = false">Cancel</Button>
        <Button variant="solid" :loading="saving" :disabled="!canSave" @click="submit">
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import api from '@/data/api'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  project: { type: String, required: true },
  currentName: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'renamed'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const input = ref(null)
const name = ref('')
const saving = ref(false)
const errorMessage = ref('')

const trimmed = computed(() => name.value.trim())
const canSave = computed(() => Boolean(trimmed.value) && trimmed.value !== props.currentName)

watch(show, async (open) => {
  if (!open) return
  name.value = props.currentName
  errorMessage.value = ''
  await nextTick()
  const el = input.value?.$el?.querySelector('input')
  el?.focus()
  el?.select()
})

async function submit() {
  if (!canSave.value || saving.value) return
  saving.value = true
  errorMessage.value = ''
  try {
    const doc = await api.updateProject(props.project, { project_name: trimmed.value })
    emit('renamed', doc)
    show.value = false
  } catch (e) {
    errorMessage.value = e?.messages?.join(', ') || e?.message || 'Could not rename the project'
  } finally {
    saving.value = false
  }
}
</script>
