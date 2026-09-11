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
