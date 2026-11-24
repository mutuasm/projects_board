import { onMounted, onUnmounted, ref } from 'vue'

/**
 * App-wide keyboard shortcuts. Deliberately ignores keystrokes aimed at an
 * input, textarea or rich-text editor so typing never triggers navigation.
 */
export const paletteOpen = ref(false)

const EDITABLE = ['INPUT', 'TEXTAREA', 'SELECT']

function isTyping(event) {
  const el = event.target
  if (!el) return false
  if (EDITABLE.includes(el.tagName)) return true
  return Boolean(el.isContentEditable || el.closest?.('.ProseMirror'))
}

export function useShortcuts(handlers = {}) {
  let chord = null
  let chordTimer = null

  function resetChord() {
    chord = null
    clearTimeout(chordTimer)
  }

  function onKeydown(event) {
    // ⌘K / Ctrl-K opens the palette even while typing - that is the convention.
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault()
      paletteOpen.value = !paletteOpen.value
      return
    }

    if (isTyping(event) || event.metaKey || event.ctrlKey || event.altKey) return

    // two-key chords, Gmail style: "g" then "p"
    if (chord === 'g') {
      const target = { h: 'goHome', p: 'goProjects', w: 'goMyWork', b: 'goBoard' }[event.key.toLowerCase()]
      resetChord()
      if (target && handlers[target]) {
        event.preventDefault()
        handlers[target]()
      }
      return
    }

    const key = event.key.toLowerCase()

    if (key === 'g') {
      chord = 'g'
      chordTimer = setTimeout(resetChord, 1200)
      return
    }

    const map = {
      c: 'create',
      n: 'create',
      '/': 'search',
      '?': 'help',
      escape: 'escape',
    }
    const action = map[key]
    if (action && handlers[action]) {
      event.preventDefault()
      handlers[action](event)
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => {
    window.removeEventListener('keydown', onKeydown)
    resetChord()
  })
}
