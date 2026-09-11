import { ref } from 'vue'

/**
 * Shared, app-wide UI state: viewport class and the mobile navigation drawer.
 *
 * The media queries are module-level singletons so every component reads the
 * same value and we register one listener per query rather than one per
 * component instance.
 */

function reactiveMediaQuery(query) {
  const matches = ref(false)
  if (typeof window === 'undefined' || !window.matchMedia) return matches

  const mql = window.matchMedia(query)
  matches.value = mql.matches
  const onChange = (event) => {
    matches.value = event.matches
  }
  // Safari < 14 only has the deprecated listener API.
  if (mql.addEventListener) mql.addEventListener('change', onChange)
  else mql.addListener(onChange)

  return matches
}

/** Below Tailwind's `lg`: the sidebar becomes an overlay drawer. */
export const isMobile = reactiveMediaQuery('(max-width: 1023px)')

/** Narrow phones, where tables have to collapse into stacked cards. */
export const isNarrow = reactiveMediaQuery('(max-width: 767px)')

/** Touch input, which needs long-press to drag so the board can still scroll. */
export const isTouch = reactiveMediaQuery('(pointer: coarse)')

export const sidebarOpen = ref(false)

export function openSidebar() {
  sidebarOpen.value = true
}

export function closeSidebar() {
  sidebarOpen.value = false
}

export function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}
