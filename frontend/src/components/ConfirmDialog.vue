<template>
  <Dialog
    v-model="confirmState.open"
    :title="confirmState.title"
    :message="confirmState.message"
    size="sm"
    :actions="[
      { label: confirmState.label, variant: 'solid', theme: confirmState.theme, onClick: run },
      { label: 'Cancel' },
    ]"
  />
</template>

<script setup>
import { Dialog } from 'frappe-ui'
import { confirmState } from '@/utils/confirm'

async function run({ close }) {
  try {
    await confirmState.onConfirm?.()
  } finally {
    close()
  }
}
</script>
