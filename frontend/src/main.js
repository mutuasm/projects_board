import './main.css'

import { createApp } from 'vue'
import {
  Button,
  Badge,
  Dialog,
  ErrorMessage,
  FormControl,
  FrappeUI,
  TextInput,
  Tooltip,
  frappeRequest,
  setConfig,
} from 'frappe-ui'

import App from './App.vue'
import router from './router'
import { session } from './data/session'

const app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
// frappe-ui 1.x opens no socket of its own; data/realtime.js runs the app's one.
app.use(FrappeUI)
app.use(router)

const globalComponents = {
  Button,
  Badge,
  Dialog,
  ErrorMessage,
  FormControl,
  TextInput,
  Tooltip,
}
for (const name in globalComponents) {
  app.component(name, globalComponents[name])
}

function start() {
  session.boot.fetch()
  app.mount('#app')
}

if (import.meta.env.DEV) {
  // In `vite dev` there is no Jinja-rendered boot payload, so pull it over the
  // proxy before mounting - otherwise every write fails the CSRF check.
  frappeRequest({
    url: '/api/method/project_board.www.project_board.get_context_for_dev',
    method: 'POST',
  })
    .then((values) => {
      for (const key in values) window[key] = values[key]
    })
    .catch(() => {})
    .finally(start)
} else {
  start()
}
