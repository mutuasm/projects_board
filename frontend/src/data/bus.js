/** Minimal pub/sub so the detail panel can tell the board a task changed. */
const listeners = new Map()

export function on(event, handler) {
  if (!listeners.has(event)) listeners.set(event, new Set())
  listeners.get(event).add(handler)
  return () => off(event, handler)
}

export function off(event, handler) {
  listeners.get(event)?.delete(handler)
}

export function emit(event, payload) {
  listeners.get(event)?.forEach((handler) => handler(payload))
}

export const EVENTS = {
  TASK_UPDATED: 'task:updated',
  TASK_CREATED: 'task:created',
  TASK_DELETED: 'task:deleted',
  PROJECT_UPDATED: 'project:updated',
}
