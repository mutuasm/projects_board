import { ref } from 'vue'
import api from './api'
import { connected, onNotification } from './realtime'

/** The current user's inbox (native Notification Log). */
export const notifications = ref([])
export const unread = ref(0)
export const loadingNotifications = ref(false)
export const hasMoreNotifications = ref(false)

const PAGE = 30

let started = false

export async function loadNotifications() {
  loadingNotifications.value = true
  try {
    const res = await api.getNotifications(PAGE)
    notifications.value = res?.items || []
    unread.value = res?.unread || 0
    hasMoreNotifications.value = notifications.value.length === PAGE
  } catch {
    // the bell just stays as it was
  } finally {
    loadingNotifications.value = false
  }
}

/** The next page of older notifications, appended as the list is scrolled. */
export async function loadMoreNotifications() {
  if (loadingNotifications.value || !hasMoreNotifications.value) return
  loadingNotifications.value = true
  try {
    const res = await api.getNotifications(PAGE, notifications.value.length)
    const seen = new Set(notifications.value.map((n) => n.name))
    const page = (res?.items || []).filter((n) => !seen.has(n.name))
    notifications.value = [...notifications.value, ...page]
    hasMoreNotifications.value = (res?.items || []).length === PAGE
  } catch {
    // try again on the next scroll
  } finally {
    loadingNotifications.value = false
  }
}

export async function markRead(item) {
  if (item.read) return
  item.read = 1
  unread.value = Math.max(unread.value - 1, 0)
  try {
    unread.value = await api.markNotificationsRead([item.name])
  } catch {
    item.read = 0
  }
}

export async function markAllRead() {
  const previous = notifications.value.map((n) => n.read)
  notifications.value.forEach((n) => (n.read = 1))
  unread.value = 0
  try {
    unread.value = await api.markNotificationsRead()
  } catch {
    notifications.value.forEach((n, i) => (n.read = previous[i]))
  }
}

/**
 * Live when the realtime server is up; otherwise check every minute and when
 * the tab comes back into view, so the badge is never far behind.
 */
export function startNotifications() {
  if (started) return
  started = true
  loadNotifications()
  onNotification(() => loadNotifications())
  setInterval(() => {
    if (!connected.value && document.visibilityState === 'visible') loadNotifications()
  }, 60_000)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') loadNotifications()
  })
}
