import { computed, ref } from 'vue'
import api from './api'

/**
 * A running timer is just bookkeeping until it stops -- on stop we write a
 * normal Timesheet entry, so nothing here needs a custom doctype. State lives
 * in localStorage so a refresh (or a crash) does not lose the elapsed time.
 */
const STORAGE_KEY = 'pb:timer'

const running = ref(load())
const now = ref(Date.now())

setInterval(() => {
  now.value = Date.now()
}, 1000)

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function persist(value) {
  try {
    if (value) localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* private mode - the timer just will not survive a reload */
  }
}

export const activeTimer = computed(() => running.value)

export const elapsedSeconds = computed(() => {
  if (!running.value) return 0
  return Math.max(0, Math.floor((now.value - running.value.startedAt) / 1000))
})

export const elapsedLabel = computed(() => {
  const total = elapsedSeconds.value
  const h = String(Math.floor(total / 3600)).padStart(2, '0')
  const m = String(Math.floor((total % 3600) / 60)).padStart(2, '0')
  const s = String(total % 60).padStart(2, '0')
  return `${h}:${m}:${s}`
})

export function isTimingTask(taskName) {
  return running.value?.task === taskName
}

export function startTimer(task) {
  running.value = {
    task: task.name,
    subject: task.subject,
    project: task.project,
    startedAt: Date.now(),
  }
  persist(running.value)
}

export function cancelTimer() {
  running.value = null
  persist(null)
}

/** Stop and file the elapsed time as a Timesheet entry. */
export async function stopTimer({ activityType, description, isBillable = 0 } = {}) {
  if (!running.value) return null

  const timer = running.value
  const hours = Math.round((elapsedSeconds.value / 3600) * 100) / 100
  // Timesheet rejects zero hours, so never file less than a rounded minute.
  const billableHours = Math.max(hours, 0.01)

  const result = await api.logTime({
    task: timer.task,
    hours: billableHours,
    description,
    from_time: new Date(timer.startedAt)
      .toISOString()
      .slice(0, 19)
      .replace('T', ' '),
    activity_type: activityType,
    is_billable: isBillable ? 1 : 0,
    submit: 1,
  })

  cancelTimer()
  return result
}
