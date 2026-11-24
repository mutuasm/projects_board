<template>
  <Popover :placement="placement">
    <template #target="{ togglePopover, isOpen }">
      <!-- the sidebar brings its own trigger; the bell is the default -->
      <slot name="target" v-bind="{ togglePopover, isOpen, unread }">
        <button
          class="relative grid size-9 shrink-0 place-items-center rounded-lg border border-outline-gray-2 text-ink-gray-7 transition-colors hover:bg-surface-gray-2"
          :aria-label="unread ? `Notifications, ${unread} unread` : 'Notifications'"
          @click="togglePopover()"
        >
          <LucideBell class="size-4" />
          <span
            v-if="unread"
            class="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-semibold tabular-nums text-white"
          >
            {{ unread > 99 ? '99+' : unread }}
          </span>
        </button>
      </slot>
    </template>

    <template #body-main="{ close }">
      <div class="flex max-h-[70vh] w-[calc(100vw-2rem)] flex-col sm:w-96">
        <div class="flex items-center gap-2 border-b border-outline-gray-2 px-4 py-3">
          <h2 class="text-sm font-semibold text-ink-gray-9">Notifications</h2>
          <span
            v-if="!connected"
            class="text-xs text-ink-gray-4"
            title="The realtime server is not reachable, so the inbox checks every minute"
          >
            · checks every minute
          </span>
          <button
            v-if="unread"
            class="ml-auto text-xs font-medium text-ink-gray-6 hover:text-ink-gray-9"
            @click="markAllRead"
          >
            Mark all read
          </button>
        </div>

        <div class="thin-scrollbar min-h-0 flex-1 overflow-y-auto">
          <button
            v-for="item in notifications"
            :key="item.name"
            class="flex w-full gap-3 border-b border-outline-gray-1 px-4 py-3 text-left last:border-b-0 hover:bg-surface-gray-1"
            :class="item.read ? '' : 'bg-surface-gray-1/60'"
            @click="openItem(item, close)"
          >
            <UserAvatar
              :user="{ full_name: item.from_full_name, user_image: item.from_user_image }"
              size="lg"
            />
            <div class="min-w-0 flex-1">
              <p
                class="text-sm leading-snug"
                :class="item.read ? 'text-ink-gray-6' : 'text-ink-gray-9'"
              >
                {{ plainText(item.subject, 200) }}
              </p>
              <p
                v-if="item.email_content && item.type !== 'Assignment'"
                class="mt-0.5 line-clamp-2 text-xs text-ink-gray-5"
              >
                {{ plainText(item.email_content, 160) }}
              </p>
              <p class="mt-1 flex items-center gap-1.5 text-xs text-ink-gray-4">
                <component :is="typeIcon(item.type)" class="size-3" />
                {{ timeAgo(item.creation) }}
              </p>
            </div>
            <span
              v-if="!item.read"
              class="mt-1.5 size-2 shrink-0 rounded-full bg-blue-500"
              aria-label="Unread"
            />
          </button>

          <LoadMore
            v-if="hasMoreNotifications"
            :loading="loadingNotifications"
            @more="loadMoreNotifications"
          />

          <div
            v-if="!notifications.length"
            class="flex flex-col items-center gap-1 px-6 py-10 text-center"
          >
            <LucideBellOff class="size-5 text-ink-gray-4" />
            <p class="text-sm text-ink-gray-6">You're all caught up</p>
            <p class="text-xs text-ink-gray-4">
              Your ERPNext notifications - mentions, assignments, shares - land here.
            </p>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Popover } from 'frappe-ui'
import LoadMore from './LoadMore.vue'
import UserAvatar from './UserAvatar.vue'
import {
  hasMoreNotifications,
  loadingNotifications,
  loadMoreNotifications,
  markAllRead,
  markRead,
  notifications,
  startNotifications,
  unread,
} from '@/data/notifications'
import { connected } from '@/data/realtime'
import { plainText, timeAgo } from '@/utils/format'

import LucideAtSign from '~icons/lucide/at-sign'
import LucideUserPlus from '~icons/lucide/user-plus'
import LucideMessageSquare from '~icons/lucide/message-square'
import LucideShare2 from '~icons/lucide/share-2'
import LucideBell from '~icons/lucide/bell'

defineProps({ placement: { type: String, default: 'bottom-end' } })

const router = useRouter()

function typeIcon(type) {
  return (
    { Mention: LucideAtSign, Assignment: LucideUserPlus, Alert: LucideMessageSquare, Share: LucideShare2 }[
      type
    ] || LucideBell
  )
}

/** Tasks open in the panel on their board; projects open their board; the rest go to Desk. */
function openItem(item, close) {
  markRead(item)
  close?.()
  if (item.document_type === 'Task' && item.project) {
    router.push({ name: 'Board', params: { project: item.project }, query: { task: item.document_name } })
  } else if (item.document_type === 'Project') {
    router.push({ name: 'Board', params: { project: item.document_name } })
  } else if (item.document_type && item.document_name) {
    const slug = item.document_type.toLowerCase().replace(/ /g, '-')
    window.open(`/desk/${slug}/${encodeURIComponent(item.document_name)}`, '_blank')
  }
}

onMounted(startNotifications)
</script>
