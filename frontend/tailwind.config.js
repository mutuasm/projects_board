import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    // frappe-ui's own source globs (src, molecules, experimental ListView)
    ...frappeUIContent,
  ],
  theme: {
    extend: {
      // iOS notch / home indicator, so the drawer and the FAB clear them.
      padding: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-right': 'env(safe-area-inset-right)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
      },
      spacing: {
        'safe-bottom': 'env(safe-area-inset-bottom)',
      },
      screens: {
        standalone: { raw: '(display-mode: standalone)' },
        // landscape phones: wide enough for the desktop layout, but with very
        // little vertical room, so secondary chrome gets dropped.
        short: { raw: '(max-height: 500px)' },
      },
    },
  },
  plugins: [],
}
