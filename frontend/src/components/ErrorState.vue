<template>
  <div class="flex h-full flex-col items-center justify-center gap-2 p-8 text-center">
    <LucideTriangleAlert class="size-8 text-ink-red-3" />
    <p class="text-base font-medium text-ink-gray-8">Something went wrong</p>
    <p class="max-w-md text-sm text-ink-gray-6">{{ message }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ error: { type: [Object, String], default: null } })

const message = computed(() => {
  if (!props.error) return ''
  if (typeof props.error === 'string') return props.error
  return (
    props.error.messages?.join(', ') ||
    props.error.message ||
    props.error.exc_type ||
    'Unknown error'
  )
})
</script>
