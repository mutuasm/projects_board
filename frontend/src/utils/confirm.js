import { reactive } from 'vue'

/**
 * One confirm dialog for the whole app (mounted in App.vue), in place of the
 * browser's window.confirm: it matches the rest of the UI, works in dark mode,
 * and keeps its button busy while the action runs.
 */
export const confirmState = reactive({
  open: false,
  title: '',
  message: '',
  label: 'Confirm',
  theme: 'gray',
  onConfirm: null,
})

/**
 * Ask before doing something that can't be undone. `onConfirm` may be async;
 * the dialog stays open, its button spinning, until it settles.
 */
export function confirmAction({ title, message = '', label = 'Confirm', theme = 'red', onConfirm }) {
  Object.assign(confirmState, { open: true, title, message, label, theme, onConfirm })
}
