import { ref } from 'vue'
import api from './api'

/** Saved filter sets, persisted per user in Frappe's List Filter doctype. */
export const savedViews = ref([])

export async function loadSavedViews() {
  savedViews.value = (await api.getSavedViews()) || []
  return savedViews.value
}

export async function saveCurrentView(label, filters) {
  const view = await api.saveView(label, filters)
  await loadSavedViews()
  return view
}

export async function removeSavedView(name) {
  await api.deleteSavedView(name)
  await loadSavedViews()
}
