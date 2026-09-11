<template>
  <Autocomplete
    :multiple="true"
    :options="userOptions"
    :model-value="modelValue"
    placeholder="Assign to…"
    @update:model-value="onUpdate"
  >
    <template #target="{ togglePopover }">
      <button
        class="flex items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-2"
        @click="togglePopover()"
      >
        <AvatarStack v-if="selectedUsers.length" :users="selectedUsers" :max="4" />
        <span v-else class="flex items-center gap-1.5 text-sm text-ink-gray-5">
          <LucideUserPlus class="size-4" />
          Unassigned
        </span>
      </button>
    </template>
    <template #item-prefix="{ option }">
      <div class="flex items-center gap-1.5">
        <LucideCheck
          class="size-3.5 shrink-0"
          :class="isSelected(option) ? 'text-ink-gray-8' : 'invisible'"
        />
        <Avatar size="sm" :label="option.label" :image="option.user_image" />
      </div>
    </template>
  </Autocomplete>
</template>

<script setup>
import { computed } from 'vue'
import { Autocomplete, Avatar } from 'frappe-ui'
import AvatarStack from './AvatarStack.vue'
import { useUsers } from '@/data/users'

const props = defineProps({
  /** Array of user emails. */
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const { users } = useUsers()

const userOptions = computed(() =>
  users.value.map((u) => ({
    label: u.full_name || u.name,
    value: u.name,
    user_image: u.user_image,
  })),
)

const selectedUsers = computed(() =>
  (props.modelValue || []).map(
    (email) =>
      users.value.find((u) => u.name === email) || { name: email, full_name: email },
  ),
)

function isSelected(option) {
  return (props.modelValue || []).includes(option.value)
}

function onUpdate(value) {
  emit(
    'update:modelValue',
    (value || []).map((v) => (typeof v === 'string' ? v : v.value)),
  )
}
</script>
