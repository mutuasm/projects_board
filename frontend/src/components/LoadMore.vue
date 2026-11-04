<template>
  <!-- sits after the last row; scrolling it into view asks for the next page -->
  <div ref="el" class="flex h-10 items-center justify-center" aria-hidden="true">
    <LoadingIndicator v-if="loading" class="size-4 text-ink-gray-4" />
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { LoadingIndicator } from 'frappe-ui'

defineProps({ loading: { type: Boolean, default: false } })
const emit = defineEmits(['more'])

const el = ref(null)
let observer = null

onMounted(() => {
  // start a little before the end so the next page is there by the time you get to it
  observer = new IntersectionObserver(
    (entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return
      emit('more')
      // still in view after the page renders (a short page, a tall screen)?
      // Observing again re-checks, so it keeps loading until the screen is full.
      nextTick(() => {
        if (!el.value || !observer) return
        observer.unobserve(el.value)
        requestAnimationFrame(() => el.value && observer?.observe(el.value))
      })
    },
    { rootMargin: '0px 0px 400px 0px' },
  )
  observer.observe(el.value)
})

onUnmounted(() => {
  observer?.disconnect()
  observer = null
})
</script>
