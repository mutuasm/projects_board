import { ref } from 'vue'
import api from './api'

export const projects = ref([])
export const loadingProjects = ref(false)

let inflight = null

export async function loadProjects({ force = false } = {}) {
  if (projects.value.length && !force) return projects.value
  if (inflight) return inflight

  loadingProjects.value = true
  inflight = api
    .getProjects({})
    .then((rows) => {
      projects.value = rows || []
      return projects.value
    })
    .finally(() => {
      loadingProjects.value = false
      inflight = null
    })

  return inflight
}

export function projectTitle(name) {
  return projects.value.find((p) => p.name === name)?.project_name || name
}
