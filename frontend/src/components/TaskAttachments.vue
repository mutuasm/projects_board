<template>
  <div class="flex flex-col gap-1.5">
    <div
      v-for="file in files"
      :key="file.name"
      class="group flex items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-1"
    >
      <LucidePaperclip class="size-3.5 shrink-0 text-ink-gray-5" />
      <a
        :href="file.file_url"
        target="_blank"
        rel="noopener"
        class="min-w-0 flex-1 truncate text-sm text-ink-gray-8 hover:underline"
      >
        {{ file.file_name }}
      </a>
      <span class="shrink-0 text-xs tabular-nums text-ink-gray-5">
        {{ fileSize(file.file_size) }}
      </span>
      <button
        v-if="!readonly"
        class="shrink-0 text-ink-gray-4 opacity-0 transition-opacity hover:text-ink-red-3 group-hover:opacity-100"
        :aria-label="`Delete ${file.file_name}`"
        @click="remove(file)"
      >
        <LucideTrash2 class="size-3.5" />
      </button>
    </div>

    <FileUploader
      v-if="!readonly"
      :upload-args="{
        doctype: 'Task',
        docname: task,
        private: true,
      }"
      @success="onUploaded"
    >
      <template #default="{ openFileSelector, uploading, progress }">
        <button
          class="flex w-fit items-center gap-1 rounded border border-dashed border-outline-gray-3 px-1.5 py-1 text-xs text-ink-gray-6 hover:border-outline-gray-4 hover:text-ink-gray-8"
          :disabled="uploading"
          @click="openFileSelector()"
        >
          <LucideUpload class="size-3" />
          {{ uploading ? `Uploading ${progress}%` : 'Attach file' }}
        </button>
      </template>
    </FileUploader>
  </div>
</template>

<script setup>
import { FileUploader, toast } from 'frappe-ui'
import api from '@/data/api'

const props = defineProps({
  files: { type: Array, default: () => [] },
  task: { type: String, required: true },
  readonly: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

function fileSize(bytes) {
  const size = Number(bytes || 0)
  if (!size) return ''
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function onUploaded(file) {
  emit('change', [file, ...props.files])
}

async function remove(file) {
  try {
    await api.deleteAttachment(file.name)
    emit(
      'change',
      props.files.filter((f) => f.name !== file.name),
    )
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not delete the file')
  }
}
</script>
