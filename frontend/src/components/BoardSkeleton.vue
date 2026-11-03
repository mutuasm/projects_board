<template>
  <!-- Mirrors the real board's geometry so nothing jumps when data lands. -->
  <div class="no-scrollbar h-full overflow-hidden">
    <div class="flex h-full items-start gap-3 p-3 sm:p-4">
      <div
        v-for="column in 4"
        :key="column"
        class="flex h-full w-[82vw] max-w-xs shrink-0 flex-col gap-2 p-1 sm:w-72 sm:max-w-none"
      >
        <div class="flex items-center gap-2 px-1 py-1.5">
          <Skeleton width="0.5rem" height="0.5rem" class-name="rounded-full" />
          <Skeleton width="5rem" height="0.6rem" />
        </div>
        <div
          v-for="card in cardsPerColumn[column - 1]"
          :key="card"
          class="pb-panel flex flex-col gap-2 !rounded-lg p-2.5"
        >
          <Skeleton :width="card % 2 ? '90%' : '70%'" height="0.7rem" />
          <div class="flex gap-1.5">
            <Skeleton width="2.5rem" height="0.9rem" />
            <Skeleton width="3rem" height="0.9rem" />
          </div>
          <div class="flex items-center justify-between">
            <Skeleton width="5rem" height="0.6rem" />
            <Skeleton width="1.25rem" height="1.25rem" class-name="rounded-full" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Skeleton from './Skeleton.vue'

// Uneven columns read as real content rather than a loading grid.
const cardsPerColumn = [4, 3, 2, 1]
</script>
