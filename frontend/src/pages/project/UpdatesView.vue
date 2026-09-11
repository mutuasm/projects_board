<template>
  <div class="thin-scrollbar h-full overflow-y-auto px-4 pb-24 pt-4 sm:px-5 sm:pb-6">
    <div class="mx-auto flex max-w-3xl flex-col gap-5">
      <!-- composer -->
      <section
        v-if="permissions.canPostUpdate"
        class="pb-panel p-4"
      >
        <h2 class="text-sm font-semibold text-ink-gray-8">Post a status update</h2>
        <p class="mt-0.5 text-xs text-ink-gray-5">
          Saved as a native Project Update, so it is visible in the desk too.
        </p>
        <FormControl
          v-model="draft"
          class="mt-3"
          type="textarea"
          :rows="4"
          placeholder="What moved this week? Anything blocked?"
        />
        <div class="mt-2 flex items-center justify-end gap-2">
          <ErrorMessage :message="errorMessage" class="mr-auto" />
          <Button variant="solid" :loading="posting" :disabled="!draft.trim()" @click="post">
            Post update
          </Button>
        </div>
      </section>

      <!-- timeline -->
      <section v-if="loading" class="flex flex-col gap-3">
        <div
          v-for="n in 3"
          :key="n"
          class="pb-panel flex flex-col gap-2 p-4"
        >
          <Skeleton width="8rem" height="0.7rem" />
          <Skeleton width="100%" height="0.7rem" />
          <Skeleton width="60%" height="0.7rem" />
        </div>
      </section>

      <EmptyState
        v-else-if="!updates.length"
        title="No updates yet"
        description="Status updates give the team a written history of how the project moved, without digging through tasks."
      >
        <template #icon><LucideMegaphone class="size-5 text-ink-gray-5" /></template>
      </EmptyState>

      <ol v-else class="flex flex-col">
        <li
          v-for="(update, index) in updates"
          :key="update.name"
          class="relative flex gap-3 pb-6 last:pb-0"
        >
          <!-- connector -->
          <span
            v-if="index < updates.length - 1"
            class="absolute left-[15px] top-9 h-full w-px bg-outline-gray-2"
          />
          <UserAvatar
            class="relative z-10"
            :user="{ full_name: update.full_name, user_image: update.user_image }"
          />
          <div class="pb-panel min-w-0 flex-1 p-3">
            <div class="flex flex-wrap items-baseline gap-x-2">
              <span class="text-sm font-medium text-ink-gray-8">{{ update.full_name }}</span>
              <span class="text-xs text-ink-gray-5">{{ formatDate(update.date) }}</span>
              <span class="text-xs text-ink-gray-4">{{ timeAgo(update.creation) }}</span>
            </div>
            <p class="mt-1.5 whitespace-pre-wrap text-sm leading-relaxed text-ink-gray-7">
              {{ update.status_text || '—' }}
            </p>
          </div>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'
import EmptyState from '@/components/EmptyState.vue'
import Skeleton from '@/components/Skeleton.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import api from '@/data/api'
import { permissions } from '@/data/session'
import { formatDate, timeAgo } from '@/utils/format'

const props = defineProps({ project: { type: String, required: true } })

const updates = ref([])
const loading = ref(true)
const draft = ref('')
const posting = ref(false)
const errorMessage = ref('')

async function load(project) {
  loading.value = true
  try {
    updates.value = (await api.getProjectUpdates(project)) || []
  } finally {
    loading.value = false
  }
}

async function post() {
  posting.value = true
  errorMessage.value = ''
  try {
    const update = await api.addProjectUpdate(props.project, draft.value)
    updates.value = [update, ...updates.value]
    draft.value = ''
    toast.success('Update posted')
  } catch (e) {
    errorMessage.value = e?.messages?.join(', ') || e?.message || 'Could not post the update'
  } finally {
    posting.value = false
  }
}

watch(() => props.project, load, { immediate: true })
</script>
