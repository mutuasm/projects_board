<template>
  <div class="thin-scrollbar h-full overflow-y-auto px-4 pb-24 pt-4 sm:px-5 sm:pb-6">
    <div class="mx-auto flex max-w-3xl flex-col gap-5">
      <CheckinSettings :project="project" @sent="load(project, { silent: true })" />

      <!-- composer -->
      <section
        v-if="permissions.canPostUpdate"
        class="pb-panel p-4"
      >
        <h2 class="text-sm-semibold text-ink-gray-8">Post a status update</h2>
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
          <!-- a scheduled check-in: one email out, each reply appended to it -->
          <template v-if="update.is_checkin">
            <span
              class="relative z-10 grid size-8 shrink-0 place-items-center rounded-full bg-surface-green-2 text-ink-green-5"
            >
              <LucideMailCheck class="size-4" />
            </span>
            <div class="pb-panel min-w-0 flex-1 p-3">
              <div class="flex flex-wrap items-baseline gap-x-2">
                <span class="text-sm-medium text-ink-gray-8">Check-in</span>
                <span class="text-xs text-ink-gray-5">{{ formatDate(update.date) }}</span>
                <span class="text-xs text-ink-gray-4">
                  {{ update.notes.length }} {{ update.notes.length === 1 ? 'reply' : 'replies' }}
                </span>
              </div>
              <ul v-if="update.notes.length" class="mt-2 flex flex-col gap-3">
                <li v-for="note in update.notes" :key="note.idx" class="flex gap-2.5">
                  <UserAvatar :user="{ full_name: note.full_name, user_image: note.user_image }" />
                  <div class="min-w-0">
                    <p class="text-xs-medium text-ink-gray-8">{{ note.full_name }}</p>
                    <p class="whitespace-pre-wrap text-sm leading-relaxed text-ink-gray-7">
                      {{ htmlToText(note.project_status) }}
                    </p>
                  </div>
                </li>
              </ul>
              <p v-else class="mt-1.5 text-sm text-ink-gray-5">
                Emailed to the team - replies appear here as they come in.
              </p>
            </div>
          </template>

          <template v-else>
            <UserAvatar
              class="relative z-10"
              :user="{ full_name: update.full_name, user_image: update.user_image }"
            />
            <div class="pb-panel min-w-0 flex-1 p-3">
              <div class="flex flex-wrap items-baseline gap-x-2">
                <span class="text-sm-medium text-ink-gray-8">{{ update.full_name }}</span>
                <span class="text-xs text-ink-gray-5">{{ formatDate(update.date) }}</span>
                <span class="text-xs text-ink-gray-4">{{ timeAgo(update.creation) }}</span>
              </div>
              <p class="mt-1.5 whitespace-pre-wrap text-sm leading-relaxed text-ink-gray-7">
                {{ htmlToText(update.status_text) || '—' }}
              </p>
            </div>
          </template>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'
import CheckinSettings from '@/components/CheckinSettings.vue'
import EmptyState from '@/components/EmptyState.vue'
import Skeleton from '@/components/Skeleton.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import api from '@/data/api'
import { permissions } from '@/data/session'
import { batched, onListUpdate } from '@/data/realtime'
import { formatDate, htmlToText, timeAgo } from '@/utils/format'

const props = defineProps({ project: { type: String, required: true } })

const updates = ref([])
const loading = ref(true)
const draft = ref('')
const posting = ref(false)
const errorMessage = ref('')

async function load(project, { silent = false } = {}) {
  if (!silent) loading.value = true
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

// new posts and email replies show up without a refresh
const reloadSoon = batched(() => load(props.project, { silent: true }), 500)
let stopLive = null
onMounted(() => (stopLive = onListUpdate('Project Update', () => reloadSoon())))
onUnmounted(() => stopLive?.())
</script>
