import { dayjs } from './format'

/**
 * Recurring tasks are Frappe Auto Repeat records. A rule here is the slice of
 * one the board edits: { frequency, repeat_on_days, repeat_on_last_day, end_date }.
 */
export const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const WORKWEEK = WEEKDAYS.slice(0, 5)

/** What the "Repeat" menu offers, mapped onto Auto Repeat's frequencies. */
export const REPEAT_PRESETS = [
  { value: 'none', label: "Doesn't repeat" },
  { value: 'daily', label: 'Every day', frequency: 'Daily' },
  { value: 'weekdays', label: 'Every weekday (Mon–Fri)', frequency: 'Weekly', days: WORKWEEK },
  { value: 'weekly', label: 'Weekly', frequency: 'Weekly' },
  { value: 'fortnightly', label: 'Every 2 weeks', frequency: 'Fortnightly' },
  { value: 'monthly', label: 'Monthly', frequency: 'Monthly' },
  { value: 'quarterly', label: 'Every 3 months', frequency: 'Quarterly' },
  { value: 'half-yearly', label: 'Every 6 months', frequency: 'Half-yearly' },
  { value: 'yearly', label: 'Yearly', frequency: 'Yearly' },
]

export const MONTHLY_FREQUENCIES = ['Monthly', 'Quarterly', 'Half-yearly', 'Yearly']

export function presetOf(rule) {
  if (!rule?.frequency) return 'none'
  if (rule.frequency === 'Weekly') {
    const days = rule.repeat_on_days || []
    return days.length === 5 && WORKWEEK.every((d) => days.includes(d)) ? 'weekdays' : 'weekly'
  }
  return REPEAT_PRESETS.find((p) => p.frequency === rule.frequency)?.value || 'none'
}

/** A fresh rule for a menu choice, anchored on the task's first date. */
export function ruleForPreset(preset, anchor, previous = null) {
  const choice = REPEAT_PRESETS.find((p) => p.value === preset)
  if (!choice?.frequency) return null
  const weekday = WEEKDAYS[(dayjs(anchor || undefined).day() + 6) % 7]
  return {
    frequency: choice.frequency,
    repeat_on_days: choice.days ? [...choice.days] : choice.frequency === 'Weekly' ? [weekday] : [],
    repeat_on_last_day: 0,
    end_date: previous?.end_date || '',
  }
}

function ordinal(n) {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}

/** "Every week on Mon, Wed · until 31 Dec 2026" */
export function describeRepeat(rule, anchor) {
  if (!rule?.frequency) return "Doesn't repeat"
  const start = dayjs(anchor || rule.start_date || undefined)
  const onDay = rule.repeat_on_last_day ? 'on the last day' : `on the ${ordinal(start.date())}`
  const days = rule.repeat_on_days || []
  const text = {
    Daily: 'Every day',
    Weekly:
      presetOf(rule) === 'weekdays'
        ? 'Every weekday'
        : days.length
          ? `Every week on ${days.map((d) => d.slice(0, 3)).join(', ')}`
          : `Every week on ${start.format('ddd')}`,
    Fortnightly: `Every 2 weeks on ${start.format('ddd')}`,
    Monthly: `Every month ${onDay}`,
    Quarterly: `Every 3 months ${onDay}`,
    'Half-yearly': `Every 6 months ${onDay}`,
    Yearly: rule.repeat_on_last_day
      ? `Every year on the last day of ${start.format('MMMM')}`
      : `Every year on ${start.format('D MMMM')}`,
  }[rule.frequency]
  return rule.end_date ? `${text} · until ${dayjs(rule.end_date).format('D MMM YYYY')}` : text
}
