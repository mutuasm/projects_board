<template>
  <div class="flex flex-wrap items-center gap-1.5">
    <Badge
      v-for="tag in modelValue"
      :key="tag"
      theme="gray"
      variant="subtle"
      size="sm"
    >
      <span class="max-w-32 truncate">{{ tag }}</span>
      <button
        v-if="!readonly"
        class="ml-1 text-ink-gray-5 hover:text-ink-gray-8"
        :aria-label="`Remove label ${tag}`"
        @click.stop="remove(tag)"
      >
        <LucideX class="size-3" />
      </button>
    </Badge>

    <Autocomplete
      v-if="!readonly"
      :options="options"
      :model-value="null"
      placeholder="Add label"
      @update:model-value="onPick"
      @update:query="(q) => (query = q)"
    >
      <template #target="{ togglePopover }">
        <button
          class="flex items-center gap-1 rounded border border-dashed border-outline-gray-3 px-1.5 py-0.5 text-xs text-ink-gray-6 hover:border-outline-gray-4 hover:text-ink-gray-8"
          @click="togglePopover()"
        >
          <LucideTag class="size-3" />
          Label
        </button>
      </template>
      <template #footer="{ togglePopover }">
        <!-- Frappe creates the Tag master on first use, so free text is fine. -->
        <Button
          v-if="canCreate"
          class="w-full"
          @click="
            () => {
              add(query)
              togglePopover()
            }
          "
        >
          Create "{{ query }}"
        </Button>
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Autocomplete, Badge, Button } from 'frappe-ui'
import api from '@/data/api'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const query = ref('')
const allTags = ref([])

const options = computed(() =>
  allTags.value
    .filter((tag) => !props.modelValue.includes(tag))
    .map((tag) => ({ label: tag, value: tag })),
)

const canCreate = computed(() => {
  const value = query.value.trim()
  return (
    value &&
    !allTags.value.some((t) => t.toLowerCase() === value.toLowerCase()) &&
    !props.modelValue.includes(value)
  )
})

function add(tag) {
  const value = (tag || '').trim()
  if (!value || props.modelValue.includes(value)) return
  emit('update:modelValue', [...props.modelValue, value])
  query.value = ''
}

function remove(tag) {
  emit(
    'update:modelValue',
    props.modelValue.filter((t) => t !== tag),
  )
}

function onPick(option) {
  if (option) add(typeof option === 'string' ? option : option.value)
}

watch(
  () => props.readonly,
  async (readonly) => {
    if (readonly || allTags.value.length) return
    allTags.value = (await api.getAllTags()) || []
  },
  { immediate: true },
)
</script>
