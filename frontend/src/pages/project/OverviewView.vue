<template>
  <div class="thin-scrollbar h-full overflow-y-auto px-4 pb-24 pt-4 sm:px-5 sm:pb-6">
    <div v-if="!stats" class="flex h-40 items-center justify-center">
      <LoadingIndicator class="size-5 text-ink-gray-5" />
    </div>

    <div v-else class="mx-auto flex max-w-6xl flex-col gap-5">
      <!-- KPI row: headline numbers are tiles, not one-bar charts -->
      <section class="grid grid-cols-2 gap-2 sm:gap-3 md:grid-cols-5">
        <StatTile label="Tasks" :value="totalTasks" :sub="`${stats.by_status.Completed || 0} done`">
          <template #icon><LucideListChecks class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
        <StatTile
          label="Overdue"
          :value="stats.overdue"
          :value-class="stats.overdue ? 'text-ink-red-3' : 'text-ink-gray-9'"
          sub="past expected end"
        >
          <template #icon><LucideClockAlert class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
        <StatTile label="Unassigned" :value="stats.unassigned" sub="open, nobody on it">
          <template #icon><LucideUserX class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
        <StatTile
          label="Blocked"
          :value="stats.blocked"
          :value-class="stats.blocked ? 'text-ink-amber-3' : 'text-ink-gray-9'"
          sub="waiting on another task"
        >
          <template #icon><LucideLock class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
        <StatTile
          label="Hours logged"
          :value="formatNumber(stats.actual_time)"
          :sub="`of ${formatNumber(stats.expected_time)} estimated`"
        >
          <template #icon><LucideTimer class="size-3.5 text-ink-gray-5" /></template>
        </StatTile>
      </section>

      <!-- completion meter: one ratio against a limit -->
      <section class="pb-panel p-4">
        <div class="flex items-baseline justify-between">
          <h2 class="text-sm font-semibold text-ink-gray-8">Completion</h2>
          <span class="text-xs text-ink-gray-5">
            % Complete Method: {{ doc?.percent_complete_method || '—' }}
          </span>
        </div>
        <div class="mt-3 flex items-center gap-3">
          <p class="text-3xl font-semibold tabular-nums text-ink-gray-9">
            {{ Math.round(stats.percent_complete) }}%
          </p>
          <div class="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-gray-2">
            <div
              class="h-full rounded-full bg-surface-green-3 transition-all"
              :style="{ width: `${stats.percent_complete}%` }"
            />
          </div>
        </div>
      </section>

      <!-- costing & billing: every figure is a native Project rollup -->
      <section
        v-if="hasFinancials"
        class="pb-panel p-4"
      >
        <div class="flex flex-wrap items-baseline justify-between gap-2">
          <h2 class="text-sm font-semibold text-ink-gray-8">Costing &amp; billing</h2>
          <span class="text-xs text-ink-gray-5">
            Rolled up from Timesheets, Sales Orders and Purchase Invoices
          </span>
        </div>

        <dl class="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
          <div v-for="item in financials" :key="item.label">
            <dt class="text-xs text-ink-gray-5">{{ item.label }}</dt>
            <dd class="text-sm font-medium tabular-nums" :class="item.className || 'text-ink-gray-9'">
              {{ item.value }}
            </dd>
          </div>
        </dl>

        <!-- billable vs billed, as a share of one another -->
        <div v-if="stats.total_billable_amount" class="mt-4">
          <div class="mb-1 flex items-baseline justify-between text-xs">
            <span class="text-ink-gray-5">Billed vs billable</span>
            <span class="tabular-nums text-ink-gray-7">{{ billedPercent }}%</span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2">
            <div
              class="h-full rounded-full bg-surface-green-3"
              :style="{ width: `${billedPercent}%` }"
            />
          </div>
        </div>
      </section>

      <div class="grid gap-5 lg:grid-cols-2">
        <!-- tasks by status -->
        <section class="pb-panel p-4">
          <h2 class="text-sm font-semibold text-ink-gray-8">Tasks by status</h2>
          <div class="mt-3 flex flex-col gap-2">
            <BarRow
              v-for="row in statusRows"
              :key="row.label"
              :label="row.label"
              :value="row.value"
              :max="maxStatus"
              :dot-class="row.dot"
            />
            <p v-if="!statusRows.length" class="text-xs text-ink-gray-5">No tasks yet.</p>
          </div>
        </section>

        <!-- tasks by priority -->
        <section class="pb-panel p-4">
          <h2 class="text-sm font-semibold text-ink-gray-8">Tasks by priority</h2>
          <div class="mt-3 flex flex-col gap-2">
            <BarRow
              v-for="row in priorityRows"
              :key="row.label"
              :label="row.label"
              :value="row.value"
              :max="maxPriority"
            />
            <p v-if="!priorityRows.length" class="text-xs text-ink-gray-5">No tasks yet.</p>
          </div>
        </section>
      </div>

      <!-- workload: a table, because each row is a person plus two numbers -->
      <section class="pb-panel p-4">
        <h2 class="text-sm font-semibold text-ink-gray-8">Workload</h2>
        <table class="mt-3 w-full text-sm">
          <thead>
            <tr class="text-xs uppercase tracking-wide text-ink-gray-5">
              <th class="pb-2 text-left font-medium">Assignee</th>
              <th class="pb-2 text-left font-medium">Open</th>
              <th class="hidden w-1/2 pb-2 text-left font-medium sm:table-cell">Load</th>
              <th class="pb-2 text-right font-medium">Done</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in stats.workload"
              :key="row.user"
              class="border-t border-outline-gray-1"
            >
              <td class="py-1.5">
                <div class="flex items-center gap-2">
                  <UserAvatar
                    :user="{ full_name: row.full_name, user_image: row.user_image }"
                    size="sm"
                  />
                  <span class="truncate text-ink-gray-8">{{ row.full_name }}</span>
                </div>
              </td>
              <td class="py-1.5 tabular-nums text-ink-gray-8">{{ row.open }}</td>
              <td class="hidden py-1.5 pr-4 sm:table-cell">
                <div class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2">
                  <div
                    class="h-full rounded-full bg-surface-blue-3"
                    :style="{ width: `${maxOpen ? (row.open / maxOpen) * 100 : 0}%` }"
                  />
                </div>
              </td>
              <td class="py-1.5 text-right tabular-nums text-ink-gray-5">{{ row.done }}</td>
            </tr>
            <tr v-if="!stats.workload.length">
              <td colspan="4" class="py-3 text-xs text-ink-gray-5">
                Nothing assigned yet.
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <div class="grid gap-5 lg:grid-cols-2">
        <!-- native project fields, read-only summary -->
        <section class="pb-panel p-4">
          <h2 class="text-sm font-semibold text-ink-gray-8">Details</h2>
          <dl class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm sm:grid-cols-2">
            <div v-for="item in details" :key="item.label">
              <dt class="text-xs text-ink-gray-5">{{ item.label }}</dt>
              <dd class="text-ink-gray-8">{{ item.value || '—' }}</dd>
            </div>
          </dl>
        </section>

        <section class="pb-panel p-4">
          <h2 class="text-sm font-semibold text-ink-gray-8">Recent activity</h2>
          <ul class="mt-3 flex flex-col gap-3">
            <li
              v-for="item in activity"
              :key="item.name"
              class="flex gap-2 text-sm"
            >
              <UserAvatar
                :user="{ full_name: item.full_name, user_image: item.user_image }"
                size="sm"
              />
              <div class="min-w-0">
                <p class="text-ink-gray-8">
                  <span class="font-medium">{{ item.full_name }}</span>
                  <span class="text-ink-gray-6">
                    {{ verb(item.comment_type) }}
                  </span>
                  <button
                    class="text-ink-gray-8 underline decoration-dotted underline-offset-2"
                    @click="openTask(item.reference_name)"
                  >
                    {{ item.task_subject }}
                  </button>
                </p>
                <p class="text-xs text-ink-gray-5">{{ timeAgo(item.creation) }}</p>
              </div>
            </li>
            <li v-if="!activity.length" class="text-xs text-ink-gray-5">
              No activity yet.
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { LoadingIndicator } from 'frappe-ui'
import BarRow from '@/components/BarRow.vue'
import StatTile from '@/components/StatTile.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import api from '@/data/api'
import { projectDoc as doc } from '@/data/board'
import { statusStyle } from '@/utils/constants'
import { formatCurrency, formatDate, formatNumber, timeAgo } from '@/utils/format'
import { openTask } from '@/utils/taskPanel'

const props = defineProps({ project: { type: String, required: true } })

const stats = ref(null)
const activity = ref([])

const totalTasks = computed(() =>
  Object.values(stats.value?.by_status || {}).reduce((a, b) => a + b, 0),
)

const statusRows = computed(() =>
  Object.entries(stats.value?.by_status || {})
    .filter(([status]) => status !== 'Template')
    .map(([status, value]) => ({
      label: statusStyle(status).label || status,
      value,
      dot: statusStyle(status).dot,
    }))
    .sort((a, b) => b.value - a.value),
)

const priorityRows = computed(() =>
  Object.entries(stats.value?.by_priority || {})
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value),
)

const maxStatus = computed(() =>
  Math.max(1, ...statusRows.value.map((r) => r.value)),
)
const maxPriority = computed(() =>
  Math.max(1, ...priorityRows.value.map((r) => r.value)),
)
const maxOpen = computed(() =>
  Math.max(1, ...(stats.value?.workload || []).map((r) => r.open)),
)

const currency = computed(() => stats.value?.currency || '')

const money = (value) => formatCurrency(value, currency.value)

const hasFinancials = computed(() =>
  [
    'estimated_costing',
    'total_costing_amount',
    'total_billable_amount',
    'total_billed_amount',
    'total_sales_amount',
    'total_purchase_cost',
  ].some((key) => Number(stats.value?.[key] || 0)),
)

const financials = computed(() => {
  const s = stats.value || {}
  return [
    { label: 'Estimated cost', value: money(s.estimated_costing) },
    { label: 'Actual cost', value: money(s.total_costing_amount) },
    { label: 'Purchase cost', value: money(s.total_purchase_cost) },
    { label: 'Material cost', value: money(s.total_consumed_material_cost) },
    { label: 'Sales order value', value: money(s.total_sales_amount) },
    { label: 'Billable', value: money(s.total_billable_amount) },
    { label: 'Billed', value: money(s.total_billed_amount) },
    {
      label: `Gross margin (${Math.round(s.per_gross_margin || 0)}%)`,
      value: money(s.gross_margin),
      className: Number(s.gross_margin) < 0 ? 'text-ink-red-3' : 'text-ink-green-3',
    },
  ]
})

const billedPercent = computed(() => {
  const s = stats.value || {}
  if (!s.total_billable_amount) return 0
  return Math.min(
    Math.round((Number(s.total_billed_amount) / Number(s.total_billable_amount)) * 100),
    100,
  )
})

const details = computed(() => [
  { label: 'Status', value: doc.value?.status },
  { label: 'Type', value: doc.value?.project_type },
  { label: 'Expected start', value: formatDate(doc.value?.expected_start_date) },
  { label: 'Expected end', value: formatDate(doc.value?.expected_end_date) },
  { label: 'Actual start', value: formatDate(doc.value?.actual_start_date) },
  { label: 'Actual end', value: formatDate(doc.value?.actual_end_date) },
  { label: 'Customer', value: doc.value?.customer },
  { label: 'Department', value: doc.value?.department },
  { label: 'Company', value: doc.value?.company },
  { label: 'Cost center', value: doc.value?.cost_center },
])

function verb(type) {
  if (type === 'Comment') return 'commented on'
  if (type === 'Created') return 'created'
  if (type === 'Assigned') return 'was assigned'
  if (type === 'Assignment Completed') return 'completed'
  return 'updated'
}

watch(
  () => props.project,
  async (name) => {
    if (!name) return
    stats.value = null
    const [s, a] = await Promise.all([
      api.getProjectStats(name),
      api.getActivity(name, 20),
    ])
    stats.value = s
    activity.value = a || []
  },
  { immediate: true },
)
</script>
