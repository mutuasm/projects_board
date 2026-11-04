<template>
  <div class="flex flex-col gap-3">
    <!-- a native select: this editor also lives inside a popover, where a
         dropdown that opens its own popup would close the popover on pick -->
    <label class="flex flex-col gap-1.5">
      <span class="text-xs text-ink-gray-5">{{ label }}</span>
      <select
        class="pb-input h-8 w-full py-0 pl-2 pr-8 text-base"
        :value="preset"
        @change="(e) => choose(e.target.value)"
      >
        <option v-for="option in presetOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
    </label>

    <template v-if="modelValue">
      <!-- weekly: which days -->
      <div v-if="modelValue.frequency === 'Weekly'">
        <p class="mb-1.5 text-xs text-ink-gray-5">On</p>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="day in WEEKDAYS"
            :key="day"
            type="button"
            class="h-8 min-w-10 rounded-lg px-2 text-sm font-medium transition-colors"
            :class="
              (modelValue.repeat_on_days || []).includes(day)
                ? 'bg-surface-gray-7 text-ink-white'
                : 'bg-surface-gray-2 text-ink-gray-7 hover:bg-surface-gray-3'
            "
            :aria-pressed="(modelValue.repeat_on_days || []).includes(day)"
            @click="toggleDay(day)"
          >
            {{ day.slice(0, 3) }}
          </button>
        </div>
      </div>

      <!-- monthly and longer: same day, or the month's last day -->
      <div v-if="MONTHLY_FREQUENCIES.includes(modelValue.frequency)" class="flex flex-wrap gap-4">
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <input
            type="radio"
            class="text-ink-gray-9 focus:ring-0"
            :checked="!modelValue.repeat_on_last_day"
            @change="update({ repeat_on_last_day: 0 })"
          />
          On the {{ anchorDay }}
        </label>
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <input
            type="radio"
            class="text-ink-gray-9 focus:ring-0"
            :checked="Boolean(modelValue.repeat_on_last_day)"
            @change="update({ repeat_on_last_day: 1 })"
          />
          On the last day of the month
        </label>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <input
            type="checkbox"
            class="rounded text-ink-gray-9 focus:ring-0"
            :checked="Boolean(modelValue.end_date)"
            @change="(e) => update({ end_date: e.target.checked ? defaultEnd : '' })"
          />
          Ends on
        </label>
        <input
          v-if="modelValue.end_date"
          type="date"
          class="pb-input h-8 px-2 text-sm"
          :min="minEnd"
          :value="modelValue.end_date"
          @change="(e) => update({ end_date: e.target.value })"
        />
        <span v-else class="text-xs text-ink-gray-5">Never ends</span>
      </div>

      <p class="flex items-start gap-1.5 text-xs text-ink-gray-5">
        <LucideRepeat class="mt-0.5 size-3.5 shrink-0" />
        <span>
          {{ describeRepeat(modelValue, anchor) }}. Each new copy is created on its day, with the
          same assignees and dates moved along.
        </span>
      </p>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { dayjs } from '@/utils/format'
import {
  describeRepeat,
  MONTHLY_FREQUENCIES,
  presetOf,
  REPEAT_PRESETS,
  ruleForPreset,
  WEEKDAYS,
} from '@/utils/repeat'

const props = defineProps({
  /** a rule, or null for "doesn't repeat" */
  modelValue: { type: Object, default: null },
  /** the task's first date: weekly/monthly rules are read from it */
  anchor: { type: String, default: '' },
  label: { type: String, default: 'Repeat' },
})
const emit = defineEmits(['update:modelValue'])

const preset = computed(() => presetOf(props.modelValue))
const presetOptions = REPEAT_PRESETS.map((p) => ({ label: p.label, value: p.value }))

const anchorDay = computed(() => {
  const d = dayjs(props.anchor || undefined).date()
  const s = ['th', 'st', 'nd', 'rd']
  const v = d % 100
  return d + (s[(v - 20) % 10] || s[v] || s[0])
})
// Auto Repeat refuses an end date of today or the start date
const minEnd = computed(() => dayjs(props.anchor || undefined).add(1, 'day').format('YYYY-MM-DD'))
const defaultEnd = computed(() => dayjs(props.anchor || undefined).add(3, 'month').format('YYYY-MM-DD'))

function choose(value) {
  emit('update:modelValue', ruleForPreset(value, props.anchor, props.modelValue))
}

function update(patch) {
  emit('update:modelValue', { ...props.modelValue, ...patch })
}

function toggleDay(day) {
  const days = new Set(props.modelValue.repeat_on_days || [])
  days.has(day) ? days.delete(day) : days.add(day)
  // a weekly rule needs at least one day
  if (!days.size) return
  update({ repeat_on_days: WEEKDAYS.filter((d) => days.has(d)) })
}
</script>
