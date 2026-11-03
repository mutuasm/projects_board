import { ref } from 'vue'
import api from './api'
import { connected, onNotification } from './realtime'

/** The current user's inbox (native Notification Log). */
export const notifications = ref([])
export const unread = ref(0)
export const loadingNotifications = ref(false)

let started = false

export async function loadNotifications() {
  loadingNotifications.value = true
  try {
    const res = await api.getNotifications(30)
    notifications.value = res?.items || []
    unread.value = res?.unread || 0
  } catch {
    // the bell just stays as it was
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
