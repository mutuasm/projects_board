/** Trailing-edge debounce, small enough not to warrant a dependency. */
export function debounce(fn, wait = 250) {
  let timer = null
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), wait)
  }
}
