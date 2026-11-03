import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import isToday from 'dayjs/plugin/isToday'
import isTomorrow from 'dayjs/plugin/isTomorrow'

dayjs.extend(relativeTime)
dayjs.extend(isToday)
dayjs.extend(isTomorrow)

export { dayjs }

export function formatDate(value, template = 'D MMM YYYY') {
  if (!value) return ''
  return dayjs(value).format(template)
}

export function formatDateTime(value) {
  if (!value) return ''
  return dayjs(value).format('D MMM YYYY, h:mm A')
}

export function timeAgo(value) {
  if (!value) return ''
  return dayjs(value).fromNow()
}

/** Short, Jira-ish due date: "Today", "Tomorrow", "12 Mar". */
export function dueLabel(value) {
  if (!value) return ''
  const d = dayjs(value)
  if (d.isToday()) return 'Today'
  if (d.isTomorrow()) return 'Tomorrow'
  return d.format(d.year() === dayjs().year() ? 'D MMM' : 'D MMM YY')
}

export function isOverdue(value, status) {
  if (!value) return false
  if (['Completed', 'Cancelled'].includes(status)) return false
  return dayjs(value).isBefore(dayjs())
}

export function initials(name) {
  if (!name) return '?'
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

export function formatNumber(value, digits = 1) {
  const n = Number(value || 0)
  if (!n) return '0'
  return n.toLocaleString(undefined, { maximumFractionDigits: digits })
}

export function formatCurrency(value, currency = '') {
  const n = Number(value || 0)
  const formatted = n.toLocaleString(undefined, { maximumFractionDigits: 2 })
  return currency ? `${currency} ${formatted}` : formatted
}

/** Strip HTML down to a one-line preview for cards and lists. */
export function plainText(html, limit = 140) {
  if (!html) return ''
  const text = html
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return text.length > limit ? `${text.slice(0, limit)}…` : text
}

/**
 * Readable text from HTML, keeping paragraph breaks - for email replies, which
 * ERPNext stores as HTML. DOMParser builds an inert document, so nothing in
 * the markup runs.
 */
export function htmlToText(html) {
  if (!html) return ''
  if (!/[<&]/.test(html)) return html
  const marked = html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|li|h[1-6]|blockquote)>/gi, '\n')
  const doc = new DOMParser().parseFromString(marked, 'text/html')
  return (doc.body.textContent || '').replace(/\n{3,}/g, '\n\n').trim()
}
