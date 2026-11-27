<template>
  <Dropdown :options="options">
    <Button variant="ghost" size="sm">
      <template #prefix><LucideBookmark class="size-3.5" /></template>
      {{ activeLabel }}
    </Button>
  </Dropdown>

  <Dialog v-model="showSave" title="Save this view" size="sm">
    <template #default>
      <FormControl
        v-model="label"
        label="View name"
        placeholder="e.g. My urgent bugs"
        @keydown.enter="save"
      />
      <p class="mt-2 text-xs text-ink-gray-5">
        Saved to your account as a Frappe List Filter, so it follows you across devices.
      </p>
      <ErrorMessage class="mt-2" :message="errorMessage" />
    </template>
    <template #actions>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button @click="showSave = false">Cancel</Button>
        <Button variant="solid" :loading="saving" @click="save">Save view</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, Dialog, Dropdown, ErrorMessage, FormControl, toast } from 'frappe-ui'
import {
  applyFilterState,
  currentFilterState,
  hasActiveFilters,
  resetFilters,
} from '@/data/board'
import { loadSavedViews, removeSavedView, saveCurrentView, savedViews } from '@/data/views'

const showSave = ref(false)
const saving = ref(false)
const label = ref('')
const errorMessage = ref('')
const activeView = ref(null)

const activeLabel = computed(() => activeView.value || 'Views')

const options = computed(() => {
  const views = savedViews.value.map((view) => ({
    label: view.label,
    onClick: () => {
      applyFilterState(view.filters)
      activeView.value = view.label
    },
  }))

  const actions = [
    {
      label: 'Save current view…',
      icon: 'lucide-bookmark',
      onClick: () => {
        label.value = ''
        errorMessage.value = ''
        showSave.value = true
      },
    },
  ]

  if (activeView.value) {
    actions.push({
      label: `Delete “${activeView.value}”`,
      icon: 'lucide-trash-2',
      onClick: remove,
    })
  }
  if (hasActiveFilters.value || activeView.value) {
    actions.push({
      label: 'Clear filters',
      icon: 'lucide-x',
      onClick: () => {
        resetFilters()
        activeView.value = null
      },
    })
  }

  return views.length ? [...views, ...actions] : actions
})

async function save() {
  if (!label.value.trim()) {
    errorMessage.value = 'Give the view a name'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await saveCurrentView(label.value.trim(), currentFilterState())
    activeView.value = label.value.trim()
    toast.success('View saved')
    showSave.value = false
  } catch (e) {
    errorMessage.value = e?.messages?.join(', ') || e?.message || 'Could not save the view'
  } finally {
    saving.value = false
  }
}

async function remove() {
  const view = savedViews.value.find((v) => v.label === activeView.value)
  if (!view) return
  await removeSavedView(view.name)
  activeView.value = null
  toast.success('View deleted')
}

onMounted(loadSavedViews)
</script>
