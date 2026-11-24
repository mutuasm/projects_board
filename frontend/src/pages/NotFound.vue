<template>
  <div class="flex h-full flex-col items-center justify-center gap-3">
    <LucideCompass class="size-10 text-ink-gray-4" />
    <p class="text-lg font-medium text-ink-gray-8">This page does not exist</p>
    <Button variant="solid" @click="$router.push({ name: 'Home' })">
      Back to home
    </Button>
  </div>
</template>
