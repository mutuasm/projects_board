<template>
  <!-- two plain elements, not <component :is="'button'">: that string resolves to
       frappe-ui's globally registered Button instead of a native button -->
  <router-link
    v-if="to"
    :to="to"
    :class="classes"
    :active-class="activeClass"
    :title="collapsed ? label : undefined"
    :aria-label="collapsed ? label : undefined"
  >
    <SidebarLinkBody />
  </router-link>
  <button
    v-else
    type="button"
    :class="classes"
    :title="collapsed ? label : undefined"
    :aria-label="collapsed ? label : undefined"
  >
    <SidebarLinkBody />
  </button>
</template>

<script setup>
import { computed, h, useSlots } from 'vue'

const props = defineProps({
  to: { type: [String, Object], default: null },
  label: { type: String, required: true },
  collapsed: { type: Boolean, default: false },
  shortcut: { type: String, default: '' },
  badge: { type: Number, default: 0 },
  // for buttons that stand for a page or panel that is open
  active: { type: Boolean, default: false },
})

const slots = useSlots()
const activeClass = '!bg-surface-elevation-3 shadow-sm'

const classes = computed(() => [
  'flex h-7.5 w-full items-center gap-2 rounded-4 px-2 text-left text-sm text-ink-gray-8 transition-colors hover:bg-surface-gray-2',
  props.collapsed && 'justify-center',
  props.active && activeClass,
])

/** Icon, label and whatever sits on the right: the same for links and buttons. */
function SidebarLinkBody() {
  const icon = h('span', { class: 'relative grid size-4 shrink-0 place-items-center text-ink-gray-8' }, [
    slots.default?.(),
    // a dot stands in for the count while the sidebar is icons-only
    props.collapsed && props.badge
      ? h('span', { class: 'absolute -right-1 -top-1 size-2 rounded-full bg-red-500' })
      : null,
  ])
  if (props.collapsed) return icon

  let suffix = slots.suffix?.()
  if (props.badge) {
    suffix = h(
      'span',
      {
        class:
          'grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-semibold tabular-nums text-white',
      },
      props.badge > 99 ? '99+' : String(props.badge),
    )
  } else if (props.shortcut) {
    suffix = h('kbd', { class: 'font-sans text-sm text-ink-gray-4' }, props.shortcut)
  }
  return [icon, h('span', { class: 'flex-1 truncate' }, props.label), suffix]
}
</script>
