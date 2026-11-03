<template>
  <section class="pb-panel p-4">
    <div class="flex flex-wrap items-start gap-3">
      <span
        class="grid size-9 shrink-0 place-items-center rounded-lg"
        :class="enabled ? 'bg-surface-green-2 text-ink-green-3' : 'bg-surface-gray-2 text-ink-gray-5'"
      >
        <LucideMailCheck class="size-[18px]" />
      </span>
      <div class="min-w-0 flex-1">
        <h2 class="flex items-center gap-2 text-sm font-semibold text-ink-gray-9">
          Automatic check-ins
          <Badge :theme="enabled ? 'green' : 'gray'" variant="subtle" size="sm">
            {{ enabled ? 'On' : 'Off' }}
          </Badge>
        </h2>
        <p class="mt-0.5 text-sm text-ink-gray-6">{{ summary }}</p>
      </div>
      <Button v-if="data?.can_edit" class="shrink-0" @click="open = !open">
        {{ open ? 'Close' : enabled ? 'Edit' : 'Set up' }}
      </Button>
    </div>

    <div v-if="open && form" class="mt-4 flex flex-col gap-4 border-t border-outline-gray-2 pt-4">
      <!-- what ERPNext needs before this can work -->
      <ul class="grid gap-2 sm:grid-cols-2">
        <li v-for="check in checks" :key="check.key" class="flex items-start gap-2 text-sm">
          <component
            :is="check.ok ? LucideCircleCheck : check.blocking ? LucideCircleX : LucideCircleAlert"
            class="mt-0.5 size-4 shrink-0"
            :class="check.ok ? 'text-ink-green-3' : check.blocking ? 'text-ink-red-3' : 'text-ink-amber-3'"
          />
          <div class="min-w-0">
            <p class="text-ink-gray-8">{{ check.label }}</p>
            <p v-if="!check.ok" class="text-xs text-ink-gray-5">
              {{ check.help }}
              <a
                v-if="check.link"
                :href="check.link"
                target="_blank"
                rel="noopener"
                class="font-medium text-ink-gray-7 underline underline-offset-2"
              >
                {{ check.linkLabel }}
              </a>
            </p>
          </div>
        </li>
      </ul>

      <FormControl
        v-model="form.collect_progress"
        type="checkbox"
        label="Email the team for a progress check-in"
      />

      <div class="grid gap-3 sm:grid-cols-3">
        <FormControl
          v-model="form.frequency"
          type="select"
          label="How often"
          :options="frequencyOptions"
        />
        <template v-if="form.frequency === 'Daily'">
          <FormControl v-model="form.daily_time_to_send" type="time" label="At" />
        </template>
        <template v-else-if="form.frequency === 'Twice Daily'">
          <FormControl v-model="form.first_email" type="time" label="First at" />
          <FormControl v-model="form.second_email" type="time" label="Second at" />
        </template>
        <template v-else-if="form.frequency === 'Weekly'">
          <FormControl v-model="form.day_to_send" type="select" label="On" :options="WEEKDAYS" />
          <FormControl v-model="form.weekly_time_to_send" type="time" label="At" />
        </template>
      </div>

      <FormControl v-model="form.subject" label="Email subject" />
      <FormControl v-model="form.message" type="textarea" label="Message" :rows="4" />

      <p class="text-xs text-ink-gray-5">
        Replies are posted here as updates. ERPNext skips a day that already has an update,
        <template v-if="data.holiday_list">and holidays in {{ data.holiday_list }},</template>
        so the team is never asked twice.
      </p>

      <ErrorMessage :message="errorMessage" />

      <div class="flex flex-wrap items-center justify-end gap-2">
        <Tooltip :text="sendBlockedReason || 'Email the check-in to the team now'">
          <Button :disabled="Boolean(sendBlockedReason)" :loading="sending" @click="sendNow">
            <template #prefix><LucideSend class="size-4" /></template>
            Send one now
          </Button>
        </Tooltip>
        <Button variant="solid" :loading="saving" @click="save">Save</Button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Badge, Button, ErrorMessage, FormControl, Tooltip, toast } from 'frappe-ui'
import api from '@/data/api'
import { projectDoc } from '@/data/board'

import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideCircleX from '~icons/lucide/circle-x'
import LucideCircleAlert from '~icons/lucide/circle-alert'

const props = defineProps({ project: { type: String, required: true } })
const emit = defineEmits(['sent'])

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const FREQUENCY_LABELS = { Daily: 'Every day', 'Twice Daily': 'Twice a day', Weekly: 'Once a week' }

const data = ref(null)
const form = ref(null)
const open = ref(false)
const saving = ref(false)
const sending = ref(false)
const errorMessage = ref('')

const enabled = computed(() => Boolean(data.value?.settings?.collect_progress))
const readiness = computed(() => data.value?.readiness || {})
const recipients = computed(() => readiness.value.recipients || [])

const frequencyOptions = computed(() =>
  (data.value?.frequencies || []).map((f) => ({ label: FREQUENCY_LABELS[f] || f, value: f })),
)

function when(s) {
  if (s.frequency === 'Daily') return `every day at ${s.daily_time_to_send || '?'}`
  if (s.frequency === 'Twice Daily') return `twice a day, at ${s.first_email || '?'} and ${s.second_email || '?'}`
  if (s.frequency === 'Weekly') return `every ${s.day_to_send || '?'} at ${s.weekly_time_to_send || '?'}`
  return 'on a schedule'
}

const summary = computed(() => {
  if (!data.value) return 'Loading…'
  const s = data.value.settings
  const people = `${recipients.value.length} team ${recipients.value.length === 1 ? 'member' : 'members'}`
  if (!enabled.value) return 'Email the team on a schedule and post their replies here automatically.'
  return `Emailed to ${people} ${when(s)}.`
})

const checks = computed(() => [
  {
    key: 'outgoing',
    ok: readiness.value.outgoing,
    blocking: true,
    label: 'Outgoing email',
    help: 'ERPNext has no default outgoing email account to send from.',
    link: '/app/email-account/new',
    linkLabel: 'Set one up in Desk',
  },
  {
    key: 'recipients',
    ok: recipients.value.length > 0,
    blocking: true,
    label: recipients.value.length
      ? `Goes to ${recipients.value.map((r) => r.full_name).join(', ')}`
      : 'Team members',
    help: 'The check-in goes to the project team, and this project has none with an email.',
    link: `/app/project/${props.project}`,
    linkLabel: 'Add them in Desk',
  },
  {
    key: 'incoming',
    ok: readiness.value.incoming,
    blocking: false,
    label: 'Replies come back',
    help: 'Without a default incoming email account, replies are not collected into Updates.',
    link: '/app/email-account',
    linkLabel: 'Email accounts',
  },
  {
    key: 'scheduler',
    ok: readiness.value.scheduler,
    blocking: true,
    label: 'Scheduler running',
    help: 'Scheduled emails only go out while the ERPNext scheduler is enabled.',
  },
])

const sendBlockedReason = computed(() => {
  if (!readiness.value.outgoing) return 'Set up outgoing email first'
  if (!recipients.value.length) return 'The project has no team members to email'
  const s = data.value?.settings || {}
  if (!s.subject || !s.message) return 'Save a subject and message first'
  return ''
})

function defaults() {
  const name = projectDoc.value?.project_name || props.project
  return {
    frequency: 'Weekly',
    day_to_send: 'Monday',
    weekly_time_to_send: '09:00',
    daily_time_to_send: '09:00',
    first_email: '09:00',
    second_email: '16:00',
    subject: `Progress check-in: ${name}`,
    message:
      "What did you get done since the last check-in, what's next, and is anything blocking you?\n\nJust reply to this email - your answer is posted to the project's Updates.",
  }
}

function fillForm() {
  const s = data.value?.settings || {}
  const d = defaults()
  form.value = {
    collect_progress: Boolean(s.collect_progress),
    // ERPNext's Hourly is not offered (see CHECKIN_FREQUENCIES on the server)
    frequency: (data.value?.frequencies || []).includes(s.frequency) ? s.frequency : d.frequency,
    day_to_send: s.day_to_send || d.day_to_send,
    weekly_time_to_send: s.weekly_time_to_send || d.weekly_time_to_send,
    daily_time_to_send: s.daily_time_to_send || d.daily_time_to_send,
    first_email: s.first_email || d.first_email,
    second_email: s.second_email || d.second_email,
    subject: s.subject || d.subject,
    message: s.message || d.message,
  }
}

async function load() {
  try {
    data.value = await api.getCheckinSettings(props.project)
    fillForm()
  } catch {
    data.value = null
  }
}

async function save() {
  saving.value = true
  errorMessage.value = ''
  try {
    data.value = await api.saveCheckinSettings(props.project, {
      ...form.value,
      collect_progress: form.value.collect_progress ? 1 : 0,
    })
    fillForm()
    toast.success(enabled.value ? 'Check-ins are on' : 'Check-in settings saved')
  } catch (e) {
    errorMessage.value = e?.messages?.join(', ') || e?.message || 'Could not save the settings'
  } finally {
    saving.value = false
  }
}

async function sendNow() {
  sending.value = true
  try {
    const res = await api.sendCheckinNow(props.project)
    toast.success(`Check-in emailed to ${res.recipients} ${res.recipients === 1 ? 'person' : 'people'}`)
    emit('sent')
  } catch (e) {
    toast.error(e?.messages?.join(', ') || e?.message || 'Could not send the check-in')
  } finally {
    sending.value = false
  }
}

watch(() => props.project, load, { immediate: true })
</script>
