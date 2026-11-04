import { computed, ref, watch } from 'vue'

/**
 * Show a long, already-loaded list a page at a time.
 *
 * `cap(groups)` trims a list of `{ tasks }` groups so that, in total, only
 * `limit` rows render - the groups stay intact, the later ones just fill in as
 * you scroll. Changing anything in `resetOn` starts again from page one.
 */
export function usePaged(pageSize = 50, resetOn = null) {
  const limit = ref(pageSize)
  if (resetOn) watch(resetOn, () => (limit.value = pageSize))

  function more() {
    limit.value += pageSize
  }

  function slice(rows) {
    return rows.slice(0, limit.value)
  }

  function cap(groups, key = 'tasks') {
    let left = limit.value
    const out = []
    for (const group of groups) {
      if (left <= 0) break
      const rows = group[key].slice(0, left)
      left -= rows.length
      out.push({ ...group, [key]: rows, total: group.total ?? group[key].length })
    }
    return out
  }

  return { limit, more, slice, cap, pageSize: computed(() => pageSize) }
}
