import { createResource } from 'frappe-ui'

/**
 * The apps on this site, from the same call the desk's apps screen uses: an app
 * shows up by declaring `add_to_apps_screen` in its hooks, and its own
 * `has_permission` check decides who sees it.
 */
export const installedApps = createResource({
  url: 'frappe.apps.get_apps',
  auto: false,
  initialData: [],
})

export function loadInstalledApps() {
  if (installedApps.fetched || installedApps.loading) return
  installedApps.fetch()
}
