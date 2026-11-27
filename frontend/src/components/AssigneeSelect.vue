<template>
  <MultiSelect
    :model-value="modelValue"
    :options="userOptions"
    placeholder="Assign to…"
    @update:model-value="onUpdate"
  >
    <!-- the trigger toggles the list itself; rows bring their own checkboxes -->
    <template #trigger>
      <button type="button" class="flex items-center gap-2 rounded-4 px-1.5 py-1 hover:bg-surface-gray-2">
        <AvatarStack v-if="selectedUsers.length" :users="selectedUsers" :max="4" />
        <span v-else class="flex items-center gap-1.5 text-sm text-ink-gray-5">
          <LucideUserPlus class="size-4" />
          Unassigned
        </span>
      </button>
    </template>
    <template #item-prefix="{ item }">
      <Avatar size="sm" :label="item.label" :image="item.user_image" />
    </template>
  </MultiSelect>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, MultiSelect } from 'frappe-ui'
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

function onUpdate(value) {
  emit(
    'update:modelValue',
    (value || []).map((v) => (typeof v === 'string' ? v : v.value)),
  )
}
</script>
