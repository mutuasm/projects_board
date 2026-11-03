import { ref } from 'vue'
import { initSocket } from 'frappe-ui'

/**
 * One socket for the whole app, on Frappe's realtime server.
 *
 * Frappe already publishes what the app needs: `list_update` whenever a
 * document is saved or deleted (desk edits included), `doc_update` /
 * `docinfo_update` to anyone watching one document, and `notification` to a
 * user when a Notification Log is created for them. Everything here is a
 * nicety on top of plain requests: if the realtime server is not running, the
 * socket gives up quietly and the app works as before.
 */
export const connected = ref(false)

let socket = null
const doctypeHandlers = new Map()
const docWatchers = new Map()

function getSocket() {
  if (socket) return socket
  socket = initSocket({ port: window.socketio_port })
  // a dead realtime server should not spam the console forever
  socket.io.reconnectionAttempts(5)

  socket.on('connect', () => {
    connected.value = true
    // rooms do not survive a reconnect
    for (const doctype of doctypeHandlers.keys()) socket.emit('doctype_subscribe', doctype)
    for (const key of docWatchers.keys()) socket.emit('doc_subscribe', ...key.split('\u0000'))
  })
  socket.on('disconnect', () => (connected.value = false))

  socket.on('list_update', (data) => {
    doctypeHandlers.get(data?.doctype)?.forEach((handler) => handler(data))
  })
  for (const event of ['doc_update', 'docinfo_update']) {
    socket.on(event, (data) => {
      // doc_update carries {doctype, name}; docinfo_update (a comment, an
      // attachment, an assignment) carries the Comment as `doc`
      const doctype = data?.doctype || data?.doc?.reference_doctype
      const name = data?.name || data?.doc?.reference_name
      docWatchers.get(`${doctype}\u0000${name}`)?.forEach((handler) => handler(event, data))
    })
  }
  return socket
}

/** Call `handler({ doctype, name, user })` whenever a `doctype` record changes. */
export function onListUpdate(doctype, handler) {
  const s = getSocket()
  if (!doctypeHandlers.has(doctype)) {
    doctypeHandlers.set(doctype, new Set())
    if (s.connected) s.emit('doctype_subscribe', doctype)
  }
  doctypeHandlers.get(doctype).add(handler)
  return () => doctypeHandlers.get(doctype)?.delete(handler)
}

/** Watch one document: `handler(event, data)` on edits and new comments. */
export function watchDoc(doctype, name, handler) {
  const s = getSocket()
  const key = `${doctype}\u0000${name}`
  if (!docWatchers.has(key)) {
    docWatchers.set(key, new Set())
    if (s.connected) s.emit('doc_subscribe', doctype, name)
  }
  docWatchers.get(key).add(handler)
  return () => {
    const set = docWatchers.get(key)
    set?.delete(handler)
    if (set && !set.size) {
      docWatchers.delete(key)
      if (s.connected) s.emit('doc_unsubscribe', doctype, name)
    }
  }
}

/** The current user's `notification` event: a new inbox item. */
export function onNotification(handler) {
  const s = getSocket()
  s.on('notification', handler)
  return () => s.off('notification', handler)
}

/**
 * Collect names from a burst of events and hand them over once it settles -
 * a bulk edit fires one event per task.
 */
export function batched(callback, wait = 400) {
  let names = new Set()
  let timer = null
  return (name) => {
    if (name) names.add(name)
    clearTimeout(timer)
    timer = setTimeout(() => {
      const batch = [...names]
      names = new Set()
      callback(batch)
    }, wait)
  }
}
