import { ref } from 'vue'
import api from './api'

const cache = ref([])
const loaded = ref(false)
let inflight = null

/** All system users, fetched once and reused by every assignee picker. */
export function useUsers() {
  if (!loaded.value && !inflight) {
    inflight = api
      .searchUsers('', 500)
      .then((rows) => {
        cache.value = rows || []
        loaded.value = true
      })
      .finally(() => {
        inflight = null
      })
  }
  return { users: cache, loaded }
}

export function findUser(email) {
  return cache.value.find((u) => u.name === email)
}
