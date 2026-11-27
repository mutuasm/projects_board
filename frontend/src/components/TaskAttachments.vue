<template>
  <div class="grid gap-2 sm:grid-cols-2">
    <div
      v-for="file in files"
      :key="file.name"
      class="pb-card group relative flex items-center gap-3 !rounded-7 p-2.5"
    >
      <span
        class="grid size-9 shrink-0 place-items-center rounded-6 text-[10px] font-bold uppercase tracking-wide text-white"
        :style="{ backgroundColor: kind(file).color }"
      >
        {{ kind(file).label }}
      </span>
      <a
        :href="file.file_url"
        target="_blank"
        rel="noopener"
        class="min-w-0 flex-1 after:absolute after:inset-0"
      >
        <p class="truncate text-sm-medium text-ink-gray-8">{{ file.file_name }}</p>
        <p class="text-xs tabular-nums text-ink-gray-5">{{ fileSize(file.file_size) || '—' }}</p>
      </a>
      <button
        v-if="!readonly"
        class="relative z-10 shrink-0 rounded-4 p-1 text-ink-gray-4 opacity-0 transition-opacity hover:text-ink-red-5 focus:opacity-100 group-hover:opacity-100"
        :aria-label="`Delete ${file.file_name}`"
        @click="remove(file)"
      >
        <LucideTrash2 class="size-3.5" />
      </button>
    </div>

    <FileUploader
      v-if="!readonly"
      doctype="Task"
      :docname="task"
      :private="true"
      @success="onUploaded"
    >
      <template #default="{ openFileSelector, uploading, progress }">
        <button
          class="flex h-full min-h-[3.75rem] w-full items-center justify-center gap-1.5 rounded-7 border border-dashed border-outline-gray-3 px-3 text-sm text-ink-gray-6 transition-colors hover:border-outline-gray-4 hover:text-ink-gray-8"
          :disabled="uploading"
          @click="openFileSelector()"
        >
          <LucidePaperclip class="size-4" />
          {{ uploading ? `Uploading ${progress}%` : 'Attach a file' }}
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

// A coloured tile per family, so a deck and a spreadsheet read apart at a glance.
const KINDS = [
  { ext: ['ppt', 'pptx', 'key'], label: 'ppt', color: '#d24726' },
  { ext: ['doc', 'docx', 'odt', 'rtf'], label: 'doc', color: '#2b579a' },
  { ext: ['xls', 'xlsx', 'csv', 'ods'], label: 'xls', color: '#217346' },
  { ext: ['pdf'], label: 'pdf', color: '#e5252a' },
  { ext: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'heic'], label: 'img', color: '#8b5cf6' },
  { ext: ['zip', 'rar', '7z', 'gz', 'tar'], label: 'zip', color: '#ca8a04' },
]

function kind(file) {
  const ext = String(file.file_name || file.file_url || '').split('.').pop().toLowerCase()
  return KINDS.find((k) => k.ext.includes(ext)) || { label: ext.slice(0, 3) || 'file', color: '#6b7280' }
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
