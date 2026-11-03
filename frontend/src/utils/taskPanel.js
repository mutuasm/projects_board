import router from '@/router'

/** The detail panel is driven by `?task=` so every task is deep-linkable. */
export function openTask(name) {
  const route = router.currentRoute.value
  router.push({ ...route, query: { ...route.query, task: name } })
}

export function closeTask() {
  const route = router.currentRoute.value
  const query = { ...route.query }
  delete query.task
  router.push({ ...route, query })
}

/**
 * Esc belongs to whatever has focus. The panel only takes it when focus is in
 * the panel itself or nowhere - not in a popover, menu or dialog opened from
 * it, which are portalled outside and close themselves.
 */
export function escapeTargetsPanel(event) {
  const target = event?.target
  if (!target || target === document.body || target === document.documentElement) return true
  return Boolean(target.closest?.('[data-task-panel]'))
}
