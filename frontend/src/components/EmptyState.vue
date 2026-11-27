<template>
  <div class="flex flex-col items-center justify-center gap-2 p-10 text-center">
    <div class="grid size-10 place-items-center rounded-full bg-surface-gray-2">
      <slot name="icon"><LucideInbox class="size-5 text-ink-gray-5" /></slot>
    </div>
    <p class="text-base-medium text-ink-gray-8">{{ title }}</p>
    <p v-if="description" class="max-w-sm text-sm text-ink-gray-5">
      {{ description }}
    </p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>
